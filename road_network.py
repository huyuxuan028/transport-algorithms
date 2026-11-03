"""ORS matrix adapter. Requires explicit real [longitude, latitude] coordinates.
No conversion of synthetic kilometre coordinates into claimed real customers.
"""
import argparse,hashlib,json,math,os,time,urllib.request
from pathlib import Path
from solver import schedule

URL='https://api.heigit.org/openrouteservice/v2/matrix/'

def build_matrices(coords,key,cache,profile='driving-car',block=25,request=None):
    if not 1<=block<=25:raise ValueError('block must be 1..25')
    if not coords or any(len(p)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in p) or not -180<=p[0]<=180 or not -90<=p[1]<=90 for p in coords):
        raise ValueError('Expected finite [longitude, latitude] pairs')
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True);n=len(coords)
    distances=[[None]*n for _ in coords];durations=[[None]*n for _ in coords]
    def live(payload):
        if not key:raise ValueError('Set ORS_API_KEY locally; never commit it')
        req=urllib.request.Request(URL+profile,data=json.dumps(payload).encode(),headers={'Authorization':key,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)
    for a in range(0,n,block):
        src=list(range(a,min(a+block,n)))
        for b in range(0,n,block):
            dst=list(range(b,min(b+block,n)));indices=list(dict.fromkeys(src+dst));lookup={v:i for i,v in enumerate(indices)}
            payload={'locations':[coords[i] for i in indices],'sources':[lookup[i] for i in src],'destinations':[lookup[i] for i in dst],'metrics':['distance','duration'],'units':'m'}
            digest=hashlib.sha256(json.dumps([URL,profile,payload],sort_keys=True).encode()).hexdigest()
            file=cache/(digest+'.json')
            if file.exists():answer=json.loads(file.read_text())
            else:
                answer=(request or live)(payload)
                file.write_text(json.dumps(answer,allow_nan=False))
                if request is None:time.sleep(1.5)
            for field,target in [('distances',distances),('durations',durations)]:
                values=answer.get(field)
                if not isinstance(values,list) or len(values)!=len(src) or any(not isinstance(row,list) or len(row)!=len(dst) for row in values):raise ValueError('Unexpected matrix shape')
                for i,u in enumerate(src):
                    for j,v in enumerate(dst):
                        value=values[i][j]
                        if not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:raise ValueError(f'Unreachable/invalid road pair {u}->{v}; no straight-line fallback')
                        target[u][v]=value
    return distances,durations

def main():
    p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,required=True);p.add_argument('--coordinates',type=Path,required=True,help='JSON list of [lon,lat], depot first, customer ID order')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--cache',type=Path,default=Path('road_cache'));p.add_argument('--profile',choices=['driving-car','driving-hgv'],default='driving-car');a=p.parse_args()
    x=json.loads(a.instance.read_text());coords=json.loads(a.coordinates.read_text())
    if len(coords)!=len(x['customers']):raise ValueError('One coordinate per customer including depot is required')
    d,t=build_matrices(coords,os.environ.get('ORS_API_KEY'),a.cache,a.profile)
    x['coordinates_lonlat']=coords;x['distance_matrix_m']=d;x['duration_matrix_s']=t
    x['road_network']={'provider':'openrouteservice','map':'OpenStreetMap contributors','profile':a.profile,'coordinates_source':a.coordinates.name,'note':'Common profile for all vehicles; vehicle dimensions and truck restrictions are not enforced.'}
    groups=[[] for _ in x['vehicles']]
    for trip in sorted(x['reference_transports'],key=lambda z:(z['vehicle'],z['start_minutes'])):groups[trip['vehicle']].append(trip['customers'])
    x['reference_transports']=schedule(groups,x)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(x,indent=2,allow_nan=False))
if __name__=='__main__':main()
