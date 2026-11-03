"""Render actual local-OSM route paths on the shared Budapest address map.
Leaflet street tiles are optional and requested only after a user click on localhost.
Offline route geometry always remains available. No route lines are invented.
"""
import argparse
import hashlib
import html
import heapq
import json
from pathlib import Path

from budapest_osm import graph_from_osm
from solver import validate_solution

COLORS = ['#0072b2', '#d55e00', '#009e73', '#cc79a7', '#b28600']


def path_to_targets(graph, source, targets):
    remaining = set(targets)-{source}
    elapsed = {source: 0.}
    parent = {}
    queue = [(0., source)]
    while queue and remaining:
        clock, u = heapq.heappop(queue)
        if clock != elapsed[u]:
            continue
        remaining.discard(u)
        for v, _, secs in graph[u]:
            cost = clock+secs
            if cost < elapsed.get(v, float('inf')):
                elapsed[v], parent[v] = cost, u
                heapq.heappush(queue, (cost, v))
    if remaining:
        raise ValueError('Unreachable route target(s): '+str(remaining))
    paths = {}
    for target in targets:
        part = [target]
        while part[-1] != source:
            part.append(parent[part[-1]])
        paths[target] = part[::-1]
    return paths


def render(instance, result, raw, output):
    info = instance['road_network']
    if info.get('provider') != 'local_osm_dijkstra':
        raise ValueError('This renderer needs the local OSM graph used for the matrix; ORS requires its own directions geometry')
    if hashlib.sha256(Path(raw).read_bytes()).hexdigest() != info['raw_sha256']:
        raise ValueError('OSM graph hash mismatch')
    trips = result['best']['transports']
    validation = validate_solution(instance, trips, result['best']['fleet'])
    nodes, graph = graph_from_osm(json.loads(Path(raw).read_text()))
    ids = instance['osm_node_ids']
    needed = {}
    for trip in trips:
        visits = [0]+trip['customers']+[0]
        for a, b in zip(visits, visits[1:]):
            needed.setdefault(ids[a], set()).add(ids[b])
    paths = {}
    for index, (source, targets) in enumerate(needed.items(), 1):
        paths[source] = path_to_targets(graph, source, targets)
        if index % 50 == 0:
            print(f'Route geometry sources: {index}/{len(needed)}', flush=True)
    routes = []
    for trip in trips:
        visits = [0]+trip['customers']+[0]
        geometry = []
        for a, b in zip(visits, visits[1:]):
            geometry.extend(nodes[u] for u in paths[ids[a]][ids[b]])
        routes.append({'vehicle': trip['vehicle'], 'stops': len(trip['customers']),
                       'distance_km': trip['distance_km'], 'points': [[p[1], p[0]] for p in geometry]})
    coords = instance['coordinates_lonlat']
    all_points = coords + [[p[1], p[0]] for r in routes for p in r['points']]
    west, east = min(p[0] for p in all_points), max(p[0] for p in all_points)
    south, north = min(p[1] for p in all_points), max(p[1] for p in all_points)
    def xy(lon, lat):
        return f'{(lon-west)/max(east-west,1e-9)*1000:.2f},{(north-lat)/max(north-south,1e-9)*800:.2f}'
    svg_routes = ''.join(f'<polyline class="v{r["vehicle"]}" points="'+
                         ' '.join(xy(p[1], p[0]) for p in r['points'])+
                         f'" fill="none" stroke="{COLORS[r["vehicle"]]}" stroke-width="2"/>' for r in routes)
    svg_stops = ''.join(f'<circle cx="{xy(*p).split(",")[0]}" cy="{xy(*p).split(",")[1]}" r="{5 if i==0 else 2}" fill="#193044"/>'
                        for i, p in enumerate(coords))
    payload = json.dumps({'coords': [[p[1], p[0]] for p in coords], 'routes': routes,
                          'addresses': ['Depot']+[c.get('address', 'Customer '+str(c['id'])) for c in instance['customers'][1:]],
                          'colors': COLORS}).replace('</', '<\\/')
    controls = ''.join(f'<label style="color:{color}"><input type="checkbox" checked onchange="toggle({i},this.checked)"> Vehicle {i+1}</label> '
                       for i, color in enumerate(COLORS))
    cost = validation['cost']
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="referrer" content="strict-origin-when-cross-origin">
<title>Shared Budapest road routes</title><style>body{font:16px system-ui;color:#193044;background:#f5f8fb;margin:24px}button{padding:10px;cursor:pointer}label{margin-right:12px}#map{height:75vh;margin-top:16px}svg.offline{width:100%;max-height:75vh;background:white;border:1px solid #b8c5d1}summary{cursor:pointer}pre{white-space:pre-wrap}</style>
<h1>Shared Budapest road routes</h1><p>__COUNT__ shared customer addresses · __VEHICLES__ available vehicles · __DIST__ km · estimated cost €__COST__</p>
<p>Local OpenStreetMap graph paths. Static estimated times; no turn-restriction or truck-clearance validation. Address-to-road offsets are audited separately.</p>
<p>Stop-count mode: __MODE__ · trips below/above range: __AUDIT__ · overtime: __OT__ h. Eight hours is the regular-wage threshold.</p>
<p>__CONTROLS__</p><button id="open" onclick="openMap()">Open routes on street map (internet)</button> <button onclick="fit()">Fit all routes</button> <span id="status">Offline route geometry is below.</span>
<div id="map" hidden></div><details open id="offline"><summary>Offline route geometry</summary><svg class="offline" viewBox="-15 -15 1030 830">__SVG__</svg></details>
<p>Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>, ODbL. Orders and address records are adopted from the PSO team's shared dataset; actual deliveries are simulated.</p>
<details><summary>Routing provenance and limitations</summary><pre>__PROVENANCE__</pre></details>
<script>const d=__DATA__;let map=null,groups=[],visible=d.colors.map(()=>true);const status=document.getElementById('status');
function toggle(k,on){visible[k]=on;document.querySelectorAll('.v'+k).forEach(e=>e.style.display=on?'':'none');if(map){if(on)groups[k].addTo(map);else map.removeLayer(groups[k]);}}
function fit(){if(map){map.invalidateSize();map.fitBounds(d.coords.concat(d.routes.flatMap(r=>r.points)),{padding:[20,20]});}}
function resource(tag,props){return new Promise((resolve,reject)=>{const el=document.createElement(tag);Object.assign(el,props);el.onload=resolve;el.onerror=reject;document.head.appendChild(el);});}
async function openMap(){if(map){fit();return;}if(!['http:','https:'].includes(location.protocol)){status.textContent='Run python serve_map.py to open this map on localhost.';return;}const button=document.getElementById('open');button.disabled=true;status.textContent='Loading street map…';try{
await Promise.all([resource('link',{rel:'stylesheet',href:'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'}),resource('script',{src:'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'})]);document.getElementById('map').hidden=false;
map=L.map('map',{preferCanvas:true});groups=d.colors.map(()=>L.layerGroup());const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'}).addTo(map);
tiles.once('tileerror',()=>{map.removeLayer(tiles);status.textContent='Street tiles unavailable; georeferenced route geometry remains visible.';});
d.routes.forEach(r=>L.polyline(r.points,{color:d.colors[r.vehicle],weight:3}).bindPopup('Vehicle '+(r.vehicle+1)+' · '+r.stops+' stops · '+r.distance_km.toFixed(2)+' km').addTo(groups[r.vehicle]));groups.forEach((g,k)=>{if(visible[k])g.addTo(map);});
d.coords.forEach((p,i)=>{const label=document.createElement('span');label.textContent=i?'Customer '+i+': '+d.addresses[i]:'Depot';L.circleMarker(p,{radius:i?3:7,color:'#193044'}).bindPopup(label).addTo(map);});
document.getElementById('offline').open=false;status.textContent='Road routes are overlaid on the street map.';requestAnimationFrame(fit);window.addEventListener('resize',fit);
}catch(e){status.textContent='Online map unavailable; use the offline geometry.';button.disabled=false;}}</script></html>'''
    replacements = {'COUNT': str(len(coords)-1), 'VEHICLES': str(len(instance['vehicles'])), 'DIST': f'{validation["distance_km"]:.2f}', 'COST': f'{cost["total_eur"]:.2f}',
                    'MODE': instance['model'].get('stop_count_mode', 'soft'),
                    'AUDIT': f'{cost["trips_below_min"]}/{cost["trips_above_max"]}',
                    'OT': f'{cost["overtime_hours"]:.2f}', 'CONTROLS': controls,
                    'SVG': svg_routes+svg_stops, 'PROVENANCE': html.escape(json.dumps(info, indent=2)), 'DATA': payload}
    for key, value in replacements.items():
        page = page.replace('__'+key+'__', value)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(page, encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--instance', type=Path, default=Path('data/shared_pso_250_road.json'))
    p.add_argument('--solution', type=Path, default=Path('generated/shared_experiments/best_solution.json'))
    p.add_argument('--raw', type=Path, default=Path('cache/budapest_city_osm.json'))
    p.add_argument('--output', type=Path, default=Path('generated/Shared_Road_Map.html'))
    a = p.parse_args()
    x = json.loads(a.instance.read_text())
    r = json.loads(a.solution.read_text())
    # Read and display the exact policy used by the experiment, not the source default.
    x['model']['stop_count_mode'] = r.get('stop_count_mode', x['model'].get('stop_count_mode', 'soft'))
    render(x, r, a.raw, a.output)


if __name__ == '__main__':
    main()
