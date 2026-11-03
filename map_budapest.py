"""Self-contained SVG map of actual OSM geometry; Leaflet/tiles are optional."""
import argparse,hashlib,html,json
from pathlib import Path
from budapest_osm import graph_from_osm,shortest
COLORS=['#0072b2','#d55e00','#009e73','#cc79a7','#b28600']

def render(x,result,raw,output):
    if hashlib.sha256(raw.read_bytes()).hexdigest()!=x['road_network']['raw_sha256']:raise ValueError('Wrong OSM graph snapshot')
    from solver import validate_solution
    validate_solution(x,result['best']['transports'],result['best']['fleet'])
    nodes,g=graph_from_osm(json.loads(raw.read_text()));selected=x['osm_node_ids'];coords=[nodes[u] for u in g];west=min(p[0] for p in coords);east=max(p[0] for p in coords);south=min(p[1] for p in coords);north=max(p[1] for p in coords)
    def point(k):
        lon,lat=nodes[k];return f'{(lon-west)/(east-west)*1000:.2f},{(north-lat)/(north-south)*800:.2f}'
    paths=[];seen=set();live_routes=[]
    for u,edges in g.items():
        for v,_,_ in edges:
            key=tuple(sorted([u,v]))
            if key in seen:continue
            seen.add(key);paths.append(f'<polyline points="{point(u)} {point(v)}" fill="none" stroke="#becad2" stroke-width="1.1"/>')
    cache={};routes=[]
    for trip in result['best']['transports']:
        sequence=[0]+trip['customers']+[0];geometry=[]
        for a,b in zip(sequence,sequence[1:]):
            source,target=selected[a],selected[b]
            if source not in cache:cache[source]=shortest(g,source)[2]
            current=target;part=[current]
            while current!=source:current=cache[source][current];part.append(current)
            geometry.extend(reversed(part))
        k=trip['vehicle'];live_routes.append({'vehicle':k,'points':[[nodes[u][1],nodes[u][0]] for u in geometry]});routes.append(f'<polyline class="v{k}" points="'+ ' '.join(point(v) for v in geometry)+f'" fill="none" stroke="{COLORS[k]}" stroke-width="2.5" opacity=".8"><title>Vehicle {k+1}; {len(trip["customers"])} stops; {trip["distance_km"]:.2f} km</title></polyline>')
    points=[f'<circle cx="{point(u).split(",")[0]}" cy="{point(u).split(",")[1]}" r="{6 if i==0 else 2.2}" fill="{ "#111" if i==0 else "#23384d"}"><title>{"Depot" if i==0 else "Simulated customer "+str(i)}</title></circle>' for i,u in enumerate(selected)]
    toggles=' '.join(f'<label style="color:{COLORS[k]}"><input type="checkbox" checked onchange="document.querySelectorAll(\'.v{k}\').forEach(e=>e.style.display=this.checked?\'\':\'none\');if(window.toggleVehicle)window.toggleVehicle({k},this.checked)">Vehicle {k+1}</label>' for k in range(5))
    payload=html.escape(json.dumps(x['road_network'],indent=2));total=result['validation']['distance_km'];cost=result['validation']['cost']['total_eur']
    policy=x['model'].get('stop_count_mode','soft');audit=result['validation']['cost']
    content=f'''<!doctype html><meta charset="utf-8"><title>Budapest / Keleti — OSM delivery routes</title><style>body{{margin:22px;font:15px system-ui;background:#f5f8fb;color:#193044}}svg.offline-map{{max-height:76vh;width:100%;background:white;border:1px solid #b8c5d1}}label{{margin-right:12px}}p{{max-width:1000px}}summary{{cursor:pointer}}</style><h1>Budapest / Keleti — OSM road routes</h1><p>Actual OpenStreetMap street geometry and directed graph paths. Furniture orders and delivery locations are simulated. Not live navigation or HGV clearance validation.</p><p>{len(selected)-1} customers · 5 vehicles · {total:.2f} km · estimated cost €{cost:.2f}</p><p>Stop-count policy: <b>{policy}</b> · trips below/above the configured range: {audit['trips_below_min']}/{audit['trips_above_max']}. Overtime is priced; driver rest/day limits are not modeled.</p><p>{toggles}</p><svg class="offline-map" viewBox="-10 -10 1020 820" aria-label="Actual OSM roads and optimized routes">{''.join(paths+routes+points)}</svg><p>Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>, ODbL. North is up. Hover on routes for trip information. The black marker is the simulated depot near Keleti.</p><details><summary>Routing assumptions and provenance</summary><pre>{payload}</pre></details>'''
    street_edges=[[[nodes[u][1],nodes[u][0]],[nodes[v][1],nodes[v][0]]] for u,v in sorted(seen)]
    live_data=json.dumps({'coords':[[p[1],p[0]] for p in x['coordinates_lonlat']],'routes':live_routes,'roads':street_edges,'colors':COLORS})
    extra="""<p><button id="online-button" type="button" onclick="enableStreetMap()">Open routes on street map (internet)</button> <button type="button" onclick="if(window.fitRoutes)window.fitRoutes()">Fit all routes</button> <span id="map-status" role="status">The OSM road graph below works without internet or external tiles.</span></p><div id="live-map" style="height:70vh;display:none"></div><script>const d="""+live_data+""";const el=document.getElementById("live-map");
const button=document.getElementById('online-button'),status=document.getElementById('map-status');
if(!['http:','https:'].includes(location.protocol)){button.disabled=true;status.textContent='Offline OSM graph mode. For optional online tiles, run: python serve_map.py';}
function enableStreetMap(){
 if(!['http:','https:'].includes(location.protocol))return;
 button.disabled=true;status.textContent='Loading interactive map; the offline graph remains available below.';
 const css=document.createElement('link');css.rel='stylesheet';css.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';const cssReady=new Promise((resolve,reject)=>{css.onload=resolve;css.onerror=reject;});document.head.appendChild(css);
 const script=document.createElement('script');script.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
 script.onerror=()=>{status.textContent='Map library unavailable. Use the offline OSM graph below.';};
 script.onload=async()=>{
  try{await cssReady;}catch(e){status.textContent='Map styles unavailable. Use the backup OSM graph.';return;}
  el.style.display='block';document.getElementById('offline-fallback').open=false;const m=L.map(el,{preferCanvas:true});m.fitBounds(d.coords,{padding:[24,24],maxZoom:17});
  window.routeMap=m;requestAnimationFrame(()=>{m.invalidateSize();m.fitBounds(d.coords,{padding:[24,24],maxZoom:17});});
  d.roads.forEach(p=>L.polyline(p,{color:'#8c9da9',weight:2}).addTo(m));
  const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',maxZoom:19});
  tiles.on('tileerror',()=>{if(m.hasLayer(tiles))m.removeLayer(tiles);status.textContent='Online tiles unavailable. The interactive OSM vector road graph remains visible. No automatic retries.';});
  tiles.on('load',()=>{if(m.hasLayer(tiles))status.textContent='Online OSM street map loaded. The road graph below is also available offline.';});
  tiles.addTo(m);
  const groups={};window.vehicleLayers=groups;for(let k=0;k<5;k++)groups['Vehicle '+(k+1)]=L.layerGroup().addTo(m);d.routes.forEach(r=>{const k=r.vehicle;groups['Vehicle '+(k+1)]??=L.layerGroup().addTo(m);L.polyline(r.points,{color:d.colors[k],weight:3}).bindPopup('Vehicle '+(k+1)).addTo(groups['Vehicle '+(k+1)]);});
  d.coords.forEach((p,i)=>L.circleMarker(p,{radius:i?3:8,color:i?'#263b50':'black'}).bindPopup(i?'Simulated customer '+i:'Simulated depot near Keleti').addTo(m));L.control.layers(null,groups).addTo(m);
  window.toggleVehicle=(k,visible)=>{const layer=groups['Vehicle '+(k+1)];if(layer){if(visible)layer.addTo(m);else m.removeLayer(layer);}};
  window.fitRoutes=()=>{m.invalidateSize();m.fitBounds(d.coords,{padding:[24,24],maxZoom:17});};
 };
 document.head.appendChild(script);
}
</script>"""
    content=content.replace('<meta charset="utf-8">','<meta charset="utf-8"><meta name="referrer" content="strict-origin-when-cross-origin">')
    content=content.replace('<svg class="offline-map" viewBox=',extra+'<details id="offline-fallback" open><summary>Backup: offline OSM road graph</summary><svg class="offline-map" viewBox=');content=content.replace('</svg>','</svg></details>')
    output.write_text(content)

def main():
    p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,default=Path('data/budapest_road.json'));p.add_argument('--solution',type=Path,default=Path('results/budapest_solution.json'));p.add_argument('--raw',type=Path,default=Path('data/budapest_osm_raw.json'));p.add_argument('--output',type=Path,default=Path('Budapest_Road_Map.html'));a=p.parse_args()
    render(json.loads(a.instance.read_text()),json.loads(a.solution.read_text()),a.raw,a.output)
if __name__=='__main__':main()
