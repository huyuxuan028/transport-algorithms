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
    toggles=' '.join(f'<label style="color:{COLORS[k]}"><input type="checkbox" checked onchange="document.querySelectorAll(\'.v{k}\').forEach(e=>e.style.display=this.checked?\'\':\'none\')">Vehicle {k+1}</label>' for k in range(5))
    payload=html.escape(json.dumps(x['road_network'],indent=2));total=result['validation']['distance_km'];cost=result['validation']['cost']['total_eur']
    policy=x['model'].get('stop_count_mode','soft');audit=result['validation']['cost']
    content=f'''<!doctype html><meta charset="utf-8"><title>Budapest / Keleti — OSM delivery routes</title><style>body{{margin:22px;font:15px system-ui;background:#f5f8fb;color:#193044}}svg{{max-height:76vh;width:100%;background:white;border:1px solid #b8c5d1}}label{{margin-right:12px}}p{{max-width:1000px}}summary{{cursor:pointer}}</style><h1>Budapest / Keleti — OSM road routes</h1><p>Actual OpenStreetMap street geometry and directed graph paths. Furniture orders and delivery locations are simulated. Not live navigation or HGV clearance validation.</p><p>{len(selected)-1} customers · 5 vehicles · {total:.2f} km · estimated cost €{cost:.2f}</p><p>Stop-count policy: <b>{policy}</b> · trips below/above the configured range: {audit['trips_below_min']}/{audit['trips_above_max']}. Overtime is priced; driver rest/day limits are not modeled.</p><p>{toggles}</p><svg viewBox="-10 -10 1020 820" aria-label="Actual OSM roads and optimized routes">{''.join(paths+routes+points)}</svg><p>Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>, ODbL. North is up. Hover on routes for trip information. The black marker is the simulated depot near Keleti.</p><details><summary>Routing assumptions and provenance</summary><pre>{payload}</pre></details>'''
    live_data=json.dumps({'coords':[[p[1],p[0]] for p in x['coordinates_lonlat']],'routes':live_routes,'colors':COLORS})
    extra="""<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><div id="live-map" style="height:75vh;display:none"></div><p>Street map above requires internet; the OSM graph map below also works offline.</p><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>if(window.L){const d="""+live_data+""";const el=document.getElementById("live-map");el.style.display="block";const m=L.map(el);L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',maxZoom:19}).addTo(m);m.fitBounds(d.coords);const groups={};d.routes.forEach(r=>{const k=r.vehicle;groups["Vehicle "+(k+1)]??=L.layerGroup().addTo(m);L.polyline(r.points,{color:d.colors[k],weight:3}).bindPopup("Vehicle "+(k+1)).addTo(groups["Vehicle "+(k+1)]);});d.coords.forEach((p,i)=>L.circleMarker(p,{radius:i?3:8,color:i?"#263b50":"black"}).bindPopup(i?"Simulated customer "+i:"Simulated depot near Keleti").addTo(m));L.control.layers(null,groups).addTo(m);}</script>"""
    content=content.replace('<svg viewBox=',extra+'<svg viewBox=')
    output.write_text(content)

def main():
    p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,default=Path('data/budapest_road.json'));p.add_argument('--solution',type=Path,default=Path('results/budapest_solution.json'));p.add_argument('--raw',type=Path,default=Path('data/budapest_osm_raw.json'));p.add_argument('--output',type=Path,default=Path('Budapest_Road_Map.html'));a=p.parse_args()
    render(json.loads(a.instance.read_text()),json.loads(a.solution.read_text()),a.raw,a.output)
if __name__=='__main__':main()
