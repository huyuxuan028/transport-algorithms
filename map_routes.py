"""Draw actual ORS road geometry over OSM; no straight polyline substitute."""
import argparse,hashlib,json,os,urllib.request
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,required=True);p.add_argument('--solution',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('road_routes.html'));p.add_argument('--cache',type=Path,default=Path('road_cache'));a=p.parse_args()
    x=json.loads(a.instance.read_text());solution=json.loads(a.solution.read_text());coords=x['coordinates_lonlat'];profile=x['road_network']['profile'];layers=[];a.cache.mkdir(exist_ok=True,parents=True)
    for trip in solution['best']['transports']:
        points=[coords[i] for i in [0]+trip['customers']+[0]];segments=[]
        # Each request has at most 50 points. Overlap endpoints to preserve continuity.
        for offset in range(0,len(points)-1,49):
            payload={'coordinates':points[offset:offset+50]};url=f'https://api.heigit.org/openrouteservice/v2/directions/{profile}/geojson'
            digest=hashlib.sha256(json.dumps([url,payload],sort_keys=True).encode()).hexdigest();file=a.cache/(digest+'.json')
            if file.exists():data=json.loads(file.read_text())
            else:
                key=os.environ.get('ORS_API_KEY')
                if not key:raise ValueError('Set ORS_API_KEY locally')
                req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Authorization':key,'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=120) as response:data=json.load(response)
                file.write_text(json.dumps(data))
            segments.extend(data['features'])
        layers.append({'vehicle':trip['vehicle'],'features':segments})
    html='''<!doctype html><meta charset="utf-8"><title>ORS road routes</title><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><style>body{margin:0;font-family:sans-serif}#map{height:92vh}p{margin:10px}</style><p>Road routes: OpenRouteService · map: © OpenStreetMap contributors. Common routing profile; no vehicle-specific truck-clearance validation.</p><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>const coords=COORDS,layers=LAYERS;const map=L.map('map');L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'}).addTo(map);map.fitBounds(coords.map(p=>[p[1],p[0]]));coords.forEach((p,i)=>L.circleMarker([p[1],p[0]],{radius:i?3:8,color:i?'#555':'black'}).bindPopup(i?'Customer '+i:'Depot').addTo(map));const colors=['#2166ac','#b2182b','#238b45','#984ea3','#e08214'];layers.forEach(t=>L.geoJSON({type:'FeatureCollection',features:t.features},{style:{color:colors[t.vehicle%5]}}).bindPopup('Vehicle '+(t.vehicle+1)).addTo(map));</script>'''
    a.output.write_text(html.replace('COORDS',json.dumps(coords)).replace('LAYERS',json.dumps(layers)))
if __name__=='__main__':main()
