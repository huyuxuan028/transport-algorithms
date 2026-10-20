"""Two-part GA for a simplified heterogeneous, multi-trip delivery problem.

Chromosome = (customer permutation, vehicle ID per customer). Each vehicle's
subsequence is split into capacity-feasible sequential depot tours by DP.
No time windows, daily horizon or geometric packing. Python standard library.
"""
import argparse,json,math,random,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
EPS=1e-7

def route_m(route,d):return sum(d[a][b] for a,b in zip([0]+route,route+[0]))

def validate_instance(inst):
    customers=inst['customers'];vehicles=inst['vehicles'];d=inst['distance_matrix_m'];n=len(customers)
    if not vehicles or n<2 or len(d)!=n or any(len(row)!=n for row in d):raise ValueError('Invalid input dimensions')
    if [c['id'] for c in customers]!=list(range(n)):raise ValueError('IDs must be contiguous; 0 is depot')
    for c in customers:
        if any(not math.isfinite(c[k]) or c[k]<0 for k in ['weight_kg','volume_m3','service_minutes']):raise ValueError('Invalid customer demand')
    if customers[0]['weight_kg'] or customers[0]['volume_m3']:raise ValueError('Depot demand must be zero')
    for v in vehicles:
        if any(not math.isfinite(v[k]) or v[k]<=0 for k in ['payload_kg','volume_m3','fuel_l_per_100km']):raise ValueError('Invalid vehicle')
    for i in range(n):
        for j in range(n):
            if not math.isfinite(d[i][j]) or d[i][j]<0 or abs(d[i][j]-d[j][i])>EPS:raise ValueError('Require finite symmetric nonnegative costs')
        if d[i][i]:raise ValueError('Distance diagonal must be zero')
    if not math.isfinite(inst['model']['schedule_average_speed_kmh']) or inst['model']['schedule_average_speed_kmh']<=0:raise ValueError('Invalid assumed average speed')
    return [[k for k,v in enumerate(vehicles) if c['weight_kg']<=v['payload_kg']+EPS and c['volume_m3']<=v['volume_m3']+EPS] for c in customers]

def split_vehicle(order,v,inst):
    """O(n^2) DP: exact contiguous trip boundaries for fixed order/allocation."""
    n=len(order)
    if not n:return []
    d=inst['distance_matrix_m'];customers=inst['customers'];dp=[math.inf]*(n+1);prev=[None]*(n+1);dp[0]=0
    for i in range(n):
        if not math.isfinite(dp[i]):continue
        w=vol=path=0.;last=0
        for j in range(i,n):
            node=order[j];w+=customers[node]['weight_kg'];vol+=customers[node]['volume_m3']
            if w>v['payload_kg']+EPS or vol>v['volume_m3']+EPS:break
            path+=d[last][node];last=node
            cost=dp[i]+path+d[node][0]
            if cost<dp[j+1]-EPS:dp[j+1]=cost;prev[j+1]=i
    if prev[n] is None:raise ValueError('Allocation contains an order larger than its vehicle')
    trips=[];j=n
    while j:
        i=prev[j];trips.append(order[i:j]);j=i
    return trips[::-1]

def two_opt(route,d,passes=1):
    r=route[:]
    for _ in range(passes):
        best_delta=-EPS;pair=None;p=[0]+r+[0]
        for i in range(len(r)-1):
            for j in range(i+1,len(r)):
                delta=d[p[i]][p[j+1]]+d[p[i+1]][p[j+2]]-d[p[i]][p[i+1]]-d[p[j+1]][p[j+2]]
                if delta<best_delta:best_delta=delta;pair=(i,j)
        if pair is None:break
        i,j=pair;r[i:j+1]=reversed(r[i:j+1])
    return r

def schedule(route_groups,inst):
    customers=inst['customers'];d=inst['distance_matrix_m'];speed=inst['model']['schedule_average_speed_kmh'];result=[]
    for k,trips in enumerate(route_groups):
        clock=0.;v=inst['vehicles'][k]
        for order in trips:
            km=route_m(order,d)/1000;duration=km/speed*60+sum(customers[i]['service_minutes'] for i in order)
            result.append({'vehicle':k,'customers':order,'start_minutes':clock,'finish_minutes':clock+duration,
                'distance_km':km,'fuel_litres':km*v['fuel_l_per_100km']/100})
            clock+=duration
    return result

def validate_solution(inst,trips):
    """Recompute capacity, coverage, distance, fuel, and nonoverlapping schedules."""
    n=len(inst['customers'])-1;visits=[];distance=fuel=0.;clocks=[0.]*len(inst['vehicles']);details=[]
    d=inst['distance_matrix_m'];c=inst['customers'];speed=inst['model']['schedule_average_speed_kmh']
    for trip in sorted(trips,key=lambda t:(t['vehicle'],t['start_minutes'])):
        if any(not math.isfinite(trip[field]) for field in ['start_minutes','finish_minutes','distance_km','fuel_litres']):raise ValueError('Nonfinite trip metric')
        k=trip['vehicle']
        if not isinstance(k,int) or not 0<=k<len(inst['vehicles']):raise ValueError('Invalid physical vehicle ID')
        v=inst['vehicles'][k];route=trip['customers']
        if not route or any(not isinstance(i,int) or not 1<=i<=n for i in route):raise ValueError('Invalid visit')
        visits.extend(route);w=sum(c[i]['weight_kg'] for i in route);vol=sum(c[i]['volume_m3'] for i in route)
        if w>v['payload_kg']+EPS or vol>v['volume_m3']+EPS:raise ValueError('Overloaded trip')
        km=route_m(route,d)/1000;litres=km*v['fuel_l_per_100km']/100
        duration=km/speed*60+sum(c[i]['service_minutes'] for i in route)
        if trip['start_minutes']<clocks[k]-EPS:raise ValueError('Overlapping trips on a physical vehicle')
        if abs(trip['finish_minutes']-trip['start_minutes']-duration)>EPS:raise ValueError('Wrong trip duration')
        if abs(trip['distance_km']-km)>EPS or abs(trip['fuel_litres']-litres)>EPS:raise ValueError('Wrong objective values')
        if not math.isfinite(trip['start_minutes']) or trip['start_minutes']<0:raise ValueError('Invalid time')
        clocks[k]=trip['finish_minutes'];distance+=km;fuel+=litres
        details.append({'vehicle':v['id'],'customers':route,'weight_kg':w,'volume_m3':vol,'distance_km':km,'fuel_litres':litres})
    if sorted(visits)!=list(range(1,n+1)):raise ValueError('Missing or duplicated customers')
    return {'feasible':True,'distance_km':distance,'fuel_litres':fuel,'trips':len(trips),
        'vehicles_used':len(set(t['vehicle'] for t in trips)),'finish_minutes_by_vehicle':clocks,'trip_details':details}

def decode(genome,inst,local_search=True):
    order,assignment=genome;n=len(inst['customers'])-1
    if sorted(order)!=list(range(1,n+1)) or len(assignment)!=n:raise ValueError('Invalid chromosome')
    groups=[];new_order=[]
    for k,v in enumerate(inst['vehicles']):
        subseq=[i for i in order if assignment[i-1]==k]
        trips=split_vehicle(subseq,v,inst)
        if local_search:trips=[two_opt(r,inst['distance_matrix_m']) for r in trips]
        groups.append(trips);new_order.extend(i for r in trips for i in r)
    if len(new_order)!=n:raise ValueError('Unknown vehicle allocation')
    trips=schedule(groups,inst)
    km=sum(t['distance_km'] for t in trips);fuel=sum(t['fuel_litres'] for t in trips)
    return {'genome':[new_order,assignment[:]],'transports':trips,'distance_km':km,'fuel_litres':fuel}

def ox(a,b,rng):
    if len(a)<2:return a[:]
    left,right=sorted(rng.sample(range(len(a)+1),2));out=[None]*len(a);out[left:right]=a[left:right]
    used=set(a[left:right]);values=[i for i in b[right:]+b[:right] if i not in used]
    for j,i in zip(list(range(right,len(a)))+list(range(left)),values):out[j]=i
    return out

def solve(inst,seed=0,population=40,generations=100,objective='fuel_litres',method='ga'):
    allowed=validate_instance(inst);n=len(inst['customers'])-1
    if any(not allowed[i] for i in range(1,n+1)):raise ValueError('An indivisible order fits no vehicle')
    if objective not in ['fuel_litres','distance'] or method not in ['ga','random'] or population<4 or generations<0:raise ValueError('Invalid search configuration')
    key='distance_km' if objective=='distance' else 'fuel_litres';rng=random.Random(seed);start=time.perf_counter();evaluations=0
    def evaluate(g):
        nonlocal evaluations
        evaluations+=1;return decode(g,inst)
    base_order=[i for trip in inst['reference_transports'] for i in trip['customers']]
    base_assign=[None]*n
    for trip in inst['reference_transports']:
        for i in trip['customers']:base_assign[i-1]=trip['vehicle']
    validate_solution(inst,inst['reference_transports'])
    base=evaluate([base_order,base_assign]);pool=[base]
    def random_genome():
        return [rng.sample(range(1,n+1),n),[rng.choice(allowed[i]) for i in range(1,n+1)]]
    for _ in range(population-1):pool.append(evaluate(random_genome()))
    pool.sort(key=lambda x:x[key]);best=pool[0];history=[{'generation':0,'objective':best[key]}]
    for generation in range(1,generations+1):
        next_pool=pool[:2]
        for _ in range(population-2):
            if method=='random':g=random_genome()
            else:
                a=min(rng.sample(pool,3),key=lambda x:x[key])['genome'];b=min(rng.sample(pool,3),key=lambda x:x[key])['genome']
                order=ox(a[0],b[0],rng) if rng.random()<.9 else a[0][:]
                assignment=[aa if rng.random()<.5 else bb for aa,bb in zip(a[1],b[1])]
                if n>1 and rng.random()<.3:
                    i,j=sorted(rng.sample(range(n),2))
                    if rng.random()<.5:order[i],order[j]=order[j],order[i]
                    else:order[i:j+1]=reversed(order[i:j+1])
                if rng.random()<.3:
                    i=rng.randrange(n);assignment[i]=rng.choice(allowed[i+1])
                g=[order,assignment]
            child=evaluate(g);next_pool.append(child)
        pool=sorted(next_pool,key=lambda x:x[key]);best=min(best,pool[0],key=lambda x:x[key])
        history.append({'generation':generation,'objective':best[key]})
    elapsed=time.perf_counter()-start
    return {'instance':inst['name'],'seed':seed,'method':method,'objective':objective,'population':population,
        'generations':generations,'evaluations':evaluations,'runtime_seconds':elapsed,
        'best':best,'baseline_decoded':base,'generated_witness':validate_solution(inst,inst['reference_transports']),
        'validation':validate_solution(inst,best['transports']),'history':history,
        'optimality_gap':None,'warning':'No certified optimum. Static aggregate-capacity proxy model; no shift limits or 3D loading.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--instance',type=Path,default=ROOT/'data/example.json')
    p.add_argument('--objective',choices=['fuel_litres','distance'],default='fuel_litres');p.add_argument('--seed',type=int,default=0)
    p.add_argument('--population',type=int,default=40);p.add_argument('--generations',type=int,default=100)
    p.add_argument('--method',choices=['ga','random'],default='ga');p.add_argument('--output',type=Path,default=ROOT/'results/solution.json');a=p.parse_args()
    result=solve(json.loads(a.instance.read_text()),a.seed,a.population,a.generations,a.objective,a.method)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:result[k] for k in ['instance','method','objective','runtime_seconds','evaluations']},indent=2))
    print(json.dumps({k:v for k,v in result['validation'].items() if k!='trip_details'},indent=2))

if __name__=='__main__':main()
