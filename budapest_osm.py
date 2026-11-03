"""Real OSM street graph scenario, no routing-service key required.
Existing furniture orders are unchanged; delivery locations are simulated OSM nodes.
This deliberately simple car graph omits turn relations and HGV restrictions.
"""
import argparse,copy,datetime,hashlib,heapq,json,math,random,re,urllib.parse,urllib.request
from pathlib import Path
from solver import schedule
BBOX=(19.075,47.495,19.085,47.505) # west,south,east,north, Budapest/Keleti
CLASSES={'motorway':60,'motorway_link':40,'trunk':50,'trunk_link':40,'primary':40,'primary_link':30,'secondary':35,'secondary_link':30,'tertiary':30,'tertiary_link':25,'residential':25,'unclassified':25,'living_street':15,'service':15}

def metres(a,b):
    lat1,lat2=map(math.radians,[a[1],b[1]]);dl=math.radians(b[0]-a[0]);dp=lat2-lat1
    h=math.sin(dp/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dl/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(h)))

def graph_from_osm(data):
    nodes={e['id']:[e['lon'],e['lat']] for e in data['elements'] if e['type']=='node'};graph={}
    for e in data['elements']:
        if e['type']!='way':continue
        t=e.get('tags',{});kind=t.get('highway');access=next((t[k] for k in ['motorcar','motor_vehicle','vehicle','access'] if k in t),'yes')
        if kind not in CLASSES or access in ['no','private','agricultural','forestry'] or t.get('area')=='yes':continue
        speed=CLASSES[kind];tag=t.get('maxspeed','');m=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(mph)?',tag)
        if m:speed=min(speed,float(m[1])*(1.609344 if m[2] else 1))
        if speed<=0:continue
        direction=t.get('oneway', 'yes' if t.get('junction')=='roundabout' or kind=='motorway' else 'no')
        for u,v in zip(e['nodes'],e['nodes'][1:]):
            if u not in nodes or v not in nodes:continue
            dist=metres(nodes[u],nodes[v]);secs=dist/speed*3.6
            graph.setdefault(u,[]);graph.setdefault(v,[])
            if direction not in ['-1','reverse']:graph[u].append((v,dist,secs))
            if direction not in ['yes','1','true']:graph[v].append((u,dist,secs))
    return nodes,graph

def component(graph,root):
    def reach(g):
        seen={root};stack=[root]
        while stack:
            for nxt in g.get(stack.pop(),[]):
                if nxt not in seen:seen.add(nxt);stack.append(nxt)
        return seen
    forward={u:[e[0] for e in es] for u,es in graph.items()};reverse={u:[] for u in graph}
    for u,vs in forward.items():
        for v in vs:reverse[v].append(u)
    return reach(forward)&reach(reverse)

def shortest(graph,source):
    time={source:0.};distance={source:0.};parent={};queue=[(0.,source)]
    while queue:
        elapsed,u=heapq.heappop(queue)
        if elapsed!=time[u]:continue
        for v,d,t in graph[u]:
            value=elapsed+t
            if value<time.get(v,math.inf):
                time[v]=value;distance[v]=distance[u]+d;parent[v]=u;heapq.heappush(queue,(value,v))
    return distance,time,parent

def download(path):
    import xml.etree.ElementTree as ET
    url='https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(map(str,BBOX))
    req=urllib.request.Request(url,headers={'User-Agent':'FurnitureTransportCourse/1.0 (small cached academic map query)'})
    with urllib.request.urlopen(req,timeout=60) as r:body=r.read()
    root=ET.fromstring(body);elements=[]
    for e in root:
        if e.tag=='node':elements.append({'type':'node','id':int(e.attrib['id']),'lon':float(e.attrib['lon']),'lat':float(e.attrib['lat'])})
        elif e.tag=='way':elements.append({'type':'way','id':int(e.attrib['id']),'nodes':[int(v.attrib['ref']) for v in e.findall('nd')],'tags':{v.attrib['k']:v.attrib['v'] for v in e.findall('tag')}})
    data={'source_url':url,'generator':'OSM API XML converted to JSON; turn relations not modeled','elements':elements}
    if not elements:raise ValueError('Empty OSM response')
    path.parent.mkdir(parents=True,exist_ok=True);path.with_suffix('.osm').write_bytes(body);path.write_text(json.dumps(data))
    return data

def build(instance,raw,output,seed=42):
    data=json.loads(raw.read_text());nodes,g=graph_from_osm(data)
    if not g:raise ValueError('OSM contains no supported drivable roads')
    depot=min(g,key=lambda k:metres(nodes[k],[19.0813,47.5002]))
    connected=component(g,depot);needed=len(instance['customers'])-1
    if len(connected)<needed+1:raise ValueError('Not enough mutually reachable nodes; adjust the graph extent')
    selected=[depot]+random.Random(seed).sample(sorted(connected-{depot}),needed)
    x=copy.deepcopy(instance);coords=[nodes[k] for k in selected];d=[];t=[]
    for source in selected:
        di,ti,_=shortest(g,source);d.append([di[k] for k in selected]);t.append([ti[k] for k in selected])
    x['name']=instance['name']+'-Budapest-OSM';x['distance_matrix_m']=d;x['duration_matrix_s']=t;x['coordinates_lonlat']=coords
    # Legacy plotting uses local km solely for point display, never for routing costs.
    x['coordinates_km']=[[(p[0]-coords[0][0])*111.32*math.cos(math.radians(coords[0][1])),(p[1]-coords[0][1])*110.574] for p in coords]
    x['osm_node_ids']=selected
    x['road_network']={'provider':'local_osm_dijkstra','map':'OpenStreetMap contributors','profile':'simplified car graph','bbox_wsen':BBOX,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'source_url':'https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(map(str,BBOX)),'location_seed':seed,'locations_are_synthetic':True,'demand_unchanged':True,'path_objective':'estimated travel time; distances measured along the same chosen paths','limitations':['No turn-restriction relations','No HGV-specific access or dimensions','No live traffic; speeds are explicit road-class assumptions capped by parseable maxspeed','Finite bounding box may exclude better paths outside it','Selected road nodes are simulated stops, not verified parking/unloading locations']}
    groups=[[] for _ in x['vehicles']]
    for trip in sorted(x['reference_transports'],key=lambda z:(z['vehicle'],z['start_minutes'])):groups[trip['vehicle']].append(trip['customers'])
    x['reference_transports']=schedule(groups,x)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(x,indent=2,allow_nan=False))
    return x

def main():
    p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,default=Path('data/benchmark_250.json'));p.add_argument('--raw',type=Path,default=Path('data/budapest_osm_raw.json'));p.add_argument('--output',type=Path,default=Path('data/budapest_road.json'));a=p.parse_args()
    if not a.raw.exists():download(a.raw)
    build(json.loads(a.instance.read_text()),a.raw,a.output)
    print('Saved actual OSM graph distances with simulated delivery locations:',a.output)
if __name__=='__main__':main()
