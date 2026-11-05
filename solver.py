"""Three-part GA for a simplified five-vehicle heterogeneous routing problem.

Chromosome = (customer permutation, physical vehicle per customer, type per
vehicle). Each vehicle's sequence is split into feasible depot tours by DP.
No time windows, daily horizon or geometric packing. Python standard library.
"""
import argparse,json,math,random,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
EPS=1e-7

def route_m(route,d):return sum(d[a][b] for a,b in zip([0]+route,route+[0]))

def make_fleet(inst,type_indices):
    types=inst['vehicle_types']
    if len(type_indices)!=inst['fleet_size'] or any(not isinstance(t,int) or not 0<=t<len(types) for t in type_indices):
        raise ValueError('Expected exactly fleet_size vehicle type choices')
    return [dict(types[t],id=f'{types[t]["id"]}-{k+1}',type_id=types[t]['id']) for k,t in enumerate(type_indices)]

def fixed_type_indices(inst):
    if inst.get('model',{}).get('fleet_mix_is_decision',True):return None
    by_id={v['id']:i for i,v in enumerate(inst['vehicle_types'])}
    return [by_id[v['type_id']] for v in inst['vehicles']]

class InfeasiblePartition(ValueError):
    """A valid chromosome has no feasible contiguous partition under hard rules."""

def stop_limits(inst):
    m=inst.get('model',{});mode=m.get('stop_count_mode','soft')
    if mode not in ('soft','hard'):raise ValueError('stop_count_mode must be soft or hard')
    lo=m.get('min_stops_per_trip',10);hi=m.get('max_stops_per_trip',50)
    if not isinstance(lo,int) or not isinstance(hi,int) or not 1<=lo<=hi:raise ValueError('Invalid stop bounds')
    # Soft mode: the minimum is priced by evaluate_costs, the maximum stays a hard limit.
    return (lo,hi) if mode=='hard' else (1,hi)

def soft_min_stops(inst):
    """Minimum stops per trip that evaluate_costs prices; 1 (no preference) in hard mode, where it is enforced."""
    m=inst.get('model',{})
    return 1 if m.get('stop_count_mode','soft')=='hard' else m.get('min_stops_per_trip',10)

def repair_short_trips(groups,inst,vehicles,volume_buffer):
    """Soft mode: dissolve each trip below the priced minimum by cheapest-insertion of all its
    customers into other trips with capacity and stop room; all-or-nothing per short trip."""
    lo=soft_min_stops(inst);_,hi=stop_limits(inst);d=inst['distance_matrix_m'];c=inst['customers']
    for k in range(len(groups)):
        for t in range(len(groups[k])):
            if not 0<len(groups[k][t])<lo:continue
            sim=[[r[:] for r in g] for g in groups];moved=True
            for i in groups[k][t]:
                best=None
                for k2,g2 in enumerate(sim):
                    v=vehicles[k2];max_vol=v['volume_m3']*(1.0-volume_buffer)
                    for t2,r in enumerate(g2):
                        if (k2,t2)==(k,t) or len(r)>=hi:continue
                        if sum(c[x]['weight_kg'] for x in r)+c[i]['weight_kg']>v['payload_kg']+EPS:continue
                        if sum(c[x]['volume_m3'] for x in r)+c[i]['volume_m3']>max_vol+EPS:continue
                        p=[0]+r+[0]
                        for pos in range(len(r)+1):
                            delta=d[p[pos]][i]+d[i][p[pos+1]]-d[p[pos]][p[pos+1]]
                            if best is None or delta<best[0]:best=(delta,k2,t2,pos)
                if best is None:moved=False;break
                sim[best[1]][best[2]].insert(best[3],i)
            if moved:sim[k][t]=[];groups=sim
    return [[r for r in g if r] for g in groups]

def feasible_types(inst,volume_buffer=None):
    buf=inst.get('model',{}).get('volume_buffer',0.0) if volume_buffer is None else volume_buffer
    return [[t for t,v in enumerate(inst['vehicle_types'])
             if c['weight_kg']<=v['payload_kg']+EPS and c['volume_m3']<=v['volume_m3']*(1.0-buf)+EPS]
            for c in inst['customers']]

def validate_instance(inst,volume_buffer=None):
    stop_limits(inst)
    buf=inst.get('model',{}).get('volume_buffer',0.0) if volume_buffer is None else volume_buffer
    if not isinstance(buf,(int,float)) or not math.isfinite(buf) or not 0<=buf<1:raise ValueError('volume_buffer must be in [0,1)')
    customers=inst['customers'];vehicles=inst['vehicles'];d=inst['distance_matrix_m'];n=len(customers)
    if not vehicles or n<2 or len(d)!=n or any(len(row)!=n for row in d):raise ValueError('Invalid input dimensions')
    if inst.get('fleet_size')!=5 or len(vehicles)!=5 or len(inst.get('vehicle_types',[]))!=3:
        raise ValueError('This experiment requires five physical vehicles chosen from three types')
    if [c['id'] for c in customers]!=list(range(n)):raise ValueError('IDs must be contiguous; 0 is depot')
    for c in customers:
        if any(not math.isfinite(c[k]) or c[k]<0 for k in ['weight_kg','volume_m3','service_minutes']):raise ValueError('Invalid customer demand')
    if customers[0]['weight_kg'] or customers[0]['volume_m3']:raise ValueError('Depot demand must be zero')
    for v in vehicles+inst['vehicle_types']:
        if any(not math.isfinite(v[k]) or v[k]<=0 for k in ['payload_kg','volume_m3','fuel_l_per_100km']):raise ValueError('Invalid vehicle')
    indices=[next((t for t,v in enumerate(inst['vehicle_types']) if v['id']==vehicle['type_id']),None) for vehicle in vehicles]
    if None in indices or vehicles!=make_fleet(inst,indices):raise ValueError('Invalid reference fleet')
    if fixed_type_indices(inst) is not None and any(
        not any(t in feasible_types(inst,volume_buffer)[i] for t in indices)
        for i in range(1,n)):
        raise ValueError('An order fits no physical vehicle in the fixed fleet')
    for i in range(n):
        for j in range(n):
            if not math.isfinite(d[i][j]) or d[i][j]<0 :raise ValueError('Require finite nonnegative distances')
        if d[i][i]:raise ValueError('Distance diagonal must be zero')
    if not math.isfinite(inst['model']['schedule_average_speed_kmh']) or inst['model']['schedule_average_speed_kmh']<=0:raise ValueError('Invalid assumed average speed')
    if 'duration_matrix_s' in inst:
        t=inst['duration_matrix_s']
        if len(t)!=n or any(len(row)!=n for row in t) or any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for row in t for v in row):
            raise ValueError('Invalid road travel-time matrix')
    return feasible_types(inst,volume_buffer)

DEFAULT_COST={'fuel_price':1.65,'wage':20.0,'overtime_mult':2.0,'shift_h':8.0,'maint':{'caddy':50.0,'sprinter':80.0,'man':120.0,'default':80.0},'volume_buffer':0.10,'min_stops':10,'max_stops':50,'min_stops_penalty_eur_per_customer':0.0}
def evaluate_costs(trips,vehicles,inst,overrides=None):
    """Compute real cost, stop penalties, and total optimization cost."""
    m=inst.get('model',{});overrides=overrides or {};cfg=dict(DEFAULT_COST,**overrides)
    fuel_price=overrides.get('fuel_price',m.get('fuel_price_eur_per_l',DEFAULT_COST['fuel_price']))
    mult=overrides.get('overtime_mult',m.get('overtime_multiplier',DEFAULT_COST['overtime_mult']))
    shift_h=overrides.get('shift_h',m.get('shift_hours',DEFAULT_COST['shift_h']))
    min_s=overrides.get('min_stops',m.get('min_stops_per_trip',DEFAULT_COST['min_stops']))
    max_s=overrides.get('max_stops',m.get('max_stops_per_trip',DEFAULT_COST['max_stops']))
    penalty_per_customer=overrides.get('min_stops_penalty_eur_per_customer',m.get('min_stops_penalty_eur_per_customer',DEFAULT_COST['min_stops_penalty_eur_per_customer']))
    by_v={k:[t for t in trips if t['vehicle']==k] for k in range(len(vehicles))}
    fuel_eur=sum(t['fuel_litres'] for t in trips)*fuel_price;wage_eur=maint_eur=ot_hours=0.0
    penalty_eur=sum(max(0, min_s - len(t["customers"])) * penalty_per_customer for t in trips)
    for k,v in enumerate(vehicles):
        v_trips=by_v[k]
        span=max([t['finish_minutes'] for t in v_trips]+[0.])/60.0
        w=overrides.get('wage',v.get('wage_eur_per_h',DEFAULT_COST['wage']))
        m_rate=v.get('maintenance_eur_per_1000km',cfg['maint'].get(v.get('type_id',''),cfg['maint']['default']))
        dist=sum(t['distance_km'] for t in v_trips)
        reg=min(span,shift_h);ot=max(0.,span-shift_h);ot_hours+=ot
        wage_eur+=(reg*w)+(ot*w*mult);maint_eur+=(dist/1000.0)*m_rate
    below=sum(1 for t in trips if len(t['customers'])<min_s);above=sum(1 for t in trips if len(t['customers'])>max_s)
    real_cost_eur=fuel_eur+wage_eur+maint_eur
    total_eur=real_cost_eur+penalty_eur
    return {'fuel_eur':round(fuel_eur,4),'wage_eur':round(wage_eur,4),'overtime_hours':round(ot_hours,4),'maintenance_eur':round(maint_eur,4),'real_cost_eur':round(real_cost_eur,4),'penalty_eur':round(penalty_eur,4),'total_eur':round(total_eur,4),'trips_below_min':below,'trips_above_max':above}

def split_vehicle(order,v,inst,volume_buffer=None):
    """O(n^2) DP: exact contiguous trip boundaries for fixed order/allocation."""
    n=len(order)
    if not n:return []
    buf=inst.get('model',{}).get('volume_buffer',0.0) if volume_buffer is None else volume_buffer;max_vol=v['volume_m3']*(1.0-buf)
    min_stops,max_stops=stop_limits(inst);soft_min=soft_min_stops(inst)
    # Lexicographic DP: fewest customers short of the soft minimum first, then metres.
    d=inst['distance_matrix_m'];customers=inst['customers'];dp=[(math.inf,math.inf)]*(n+1);prev=[None]*(n+1);dp[0]=(0,0.)
    for i in range(n):
        if not math.isfinite(dp[i][1]):continue
        w=vol=path=0.;last=0
        for j in range(i,n):
            if j-i+1>max_stops:break
            node=order[j];w+=customers[node]['weight_kg'];vol+=customers[node]['volume_m3']
            if w>v['payload_kg']+EPS or vol>max_vol+EPS:break
            path+=d[last][node];last=node
            if j-i+1<min_stops:continue
            short=dp[i][0]+max(0,soft_min-(j-i+1));cost=dp[i][1]+path+d[node][0]
            if short<dp[j+1][0] or (short==dp[j+1][0] and cost<dp[j+1][1]-EPS):dp[j+1]=(short,cost);prev[j+1]=i
    if prev[n] is None:raise InfeasiblePartition('No capacity- and stop-feasible partition for this vehicle sequence')
    trips=[];j=n
    while j:
        i=prev[j];trips.append(order[i:j]);j=i
    return trips[::-1]

def two_opt(route,d,passes=1):
    """One best reversal per pass; internal reversed arcs count on directed roads."""
    r=route[:]
    for _ in range(passes):
        p=[0]+r+[0];prefix=[0.0]
        for k in range(len(p)-1):
            prefix.append(prefix[-1]+d[p[k+1]][p[k]]-d[p[k]][p[k+1]])
        best_delta=-EPS;pair=None
        for i in range(len(r)-1):
            for j in range(i+1,len(r)):
                delta=(d[p[i]][p[j+1]]+d[p[i+1]][p[j+2]]
                       -d[p[i]][p[i+1]]-d[p[j+1]][p[j+2]]
                       +prefix[j+1]-prefix[i+1])
                if delta<best_delta:best_delta=delta;pair=(i,j)
        if pair is None:break
        i,j=pair;r[i:j+1]=reversed(r[i:j+1])
    return r

def travel_minutes(route,inst,vehicle):
    if 'duration_matrix_s' in inst:
        return route_m(route,inst['duration_matrix_s'])/60.0
    return route_m(route,inst['distance_matrix_m'])/1000/vehicle.get('speed_kmh',inst['model']['schedule_average_speed_kmh'])*60

def schedule(route_groups,inst,vehicles=None):
    customers=inst['customers'];d=inst['distance_matrix_m'];result=[]
    vehicles=inst['vehicles'] if vehicles is None else vehicles
    for k,trips in enumerate(route_groups):
        clock=0.;v=vehicles[k];speed=v.get('speed_kmh',inst['model']['schedule_average_speed_kmh'])
        for order in trips:
            km=route_m(order,d)/1000;duration=travel_minutes(order,inst,v)+sum(customers[i]['service_minutes'] for i in order)
            result.append({'vehicle':k,'customers':order,'start_minutes':clock,'finish_minutes':clock+duration,
                           'distance_km':km,'fuel_litres':km*v['fuel_l_per_100km']/100})
            clock+=duration
    return result

def validate_solution(inst,trips,vehicles=None,volume_buffer=None,cost_overrides=None):
    """Recompute capacity, coverage, distance, fuel, and nonoverlapping schedules."""
    vehicles=inst['vehicles'] if vehicles is None else vehicles
    if len(vehicles)!=inst['fleet_size']:raise ValueError('Wrong fleet size')
    if fixed_type_indices(inst) is not None and vehicles!=inst['vehicles']:
        raise ValueError('Solution changes the given fixed fleet')
    buf=inst.get('model',{}).get('volume_buffer',0.0) if volume_buffer is None else volume_buffer
    min_stops,max_stops=stop_limits(inst)
    n=len(inst['customers'])-1;visits=[];distance=fuel=0.;clocks=[0.]*len(vehicles);details=[]
    d=inst['distance_matrix_m'];c=inst['customers']
    for trip in sorted(trips,key=lambda t:(t['vehicle'],t['start_minutes'])):
        if any(not math.isfinite(trip[field]) for field in ['start_minutes','finish_minutes','distance_km','fuel_litres']):raise ValueError('Nonfinite trip metric')
        k=trip['vehicle']
        if not isinstance(k,int) or not 0<=k<len(vehicles):raise ValueError('Invalid physical vehicle ID')
        v=vehicles[k];route=trip['customers'];speed=v.get('speed_kmh',inst['model']['schedule_average_speed_kmh'])
        if not route or any(not isinstance(i,int) or not 1<=i<=n for i in route):raise ValueError('Invalid visit')
        if not min_stops<=len(route)<=max_stops:raise ValueError('Hard stop-count violation')
        visits.extend(route);w=sum(c[i]['weight_kg'] for i in route);vol=sum(c[i]['volume_m3'] for i in route)
        if w>v['payload_kg']+EPS or vol>(v['volume_m3']*(1.0-buf))+EPS:raise ValueError('Overloaded trip')
        km=route_m(route,d)/1000;litres=km*v['fuel_l_per_100km']/100
        duration=travel_minutes(route,inst,v)+sum(c[i]['service_minutes'] for i in route)
        if trip['start_minutes']<clocks[k]-EPS:raise ValueError('Overlapping trips on a physical vehicle')
        if abs(trip['finish_minutes']-trip['start_minutes']-duration)>EPS:raise ValueError('Wrong trip duration')
        if abs(trip['distance_km']-km)>EPS or abs(trip['fuel_litres']-litres)>EPS:raise ValueError('Wrong objective values')
        if not math.isfinite(trip['start_minutes']) or trip['start_minutes']<0:raise ValueError('Invalid time')
        clocks[k]=trip['finish_minutes'];distance+=km;fuel+=litres
        details.append({'vehicle':v['id'],'customers':route,'weight_kg':w,'volume_m3':vol,'distance_km':km,'fuel_litres':litres})
    if sorted(visits)!=list(range(1,n+1)):raise ValueError('Missing or duplicated customers')
    cost=evaluate_costs(trips,vehicles,inst,cost_overrides)
    return {'feasible':True,'distance_km':distance,'fuel_litres':fuel,'trips':len(trips),
        'fleet_type_ids':[v['type_id'] for v in vehicles],
        'vehicles_used':len(set(t['vehicle'] for t in trips)),'finish_minutes_by_vehicle':clocks,
        'trip_details':details,'cost':cost}

def decode(genome,inst,local_search=True,volume_buffer=None,cost_overrides=None,search_objective='distance'):
    order,assignment,type_indices=genome;n=len(inst['customers'])-1
    if sorted(order)!=list(range(1,n+1)) or len(assignment)!=n:raise ValueError('Invalid chromosome')
    fixed=fixed_type_indices(inst)
    if fixed is not None and type_indices!=fixed:raise ValueError('Chromosome changes the given fixed fleet')
    vehicles=inst['vehicles'] if fixed is not None else make_fleet(inst,type_indices)
    buf=inst.get('model',{}).get('volume_buffer',0.0) if volume_buffer is None else volume_buffer
    if any(not isinstance(k,int) or not 0<=k<len(vehicles) or
           inst['customers'][i]['weight_kg']>vehicles[k]['payload_kg']+EPS or
           inst['customers'][i]['volume_m3']>(vehicles[k]['volume_m3']*(1.0-buf))+EPS
           for i,k in enumerate(assignment,1)):raise ValueError('Invalid or incompatible vehicle allocation')
    groups=[];new_order=[]
    for k,v in enumerate(vehicles):
        subseq=[i for i in order if assignment[i-1]==k]
        trips=split_vehicle(subseq,v,inst,volume_buffer=buf)
        if local_search:
            improved=[two_opt(r,inst['distance_matrix_m']) for r in trips]
            if search_objective=='cost':
                # Reject distance improvements that increase time-dependent wages.
                def vehicle_cost(routes):
                    rg=[[] for _ in vehicles];rg[k]=routes
                    return evaluate_costs(schedule(rg,inst,vehicles),vehicles,inst,cost_overrides)['total_eur']
                if vehicle_cost(improved)<=vehicle_cost(trips)+EPS:trips=improved
            else:trips=improved
        groups.append(trips)
    if inst.get('model',{}).get('stop_count_mode','soft')!='hard':groups=repair_short_trips(groups,inst,vehicles,buf)
    assignment=assignment[:]
    for k,g in enumerate(groups):
        for r in g:
            new_order.extend(r)
            for i in r:assignment[i-1]=k
    if len(new_order)!=n:raise ValueError('Unknown vehicle allocation')
    trips=schedule(groups,inst,vehicles)
    km=sum(t['distance_km'] for t in trips);fuel=sum(t['fuel_litres'] for t in trips)
    cost=evaluate_costs(trips,vehicles,inst,cost_overrides)
    return {'genome':[new_order,assignment[:],type_indices[:]],'fleet':vehicles,
        'transports':trips,'distance_km':km,'fuel_litres':fuel,'cost':cost,'total_eur':cost['total_eur']}

def ox(a,b,rng):
    if len(a)<2:return a[:]
    left,right=sorted(rng.sample(range(len(a)+1),2));out=[None]*len(a);out[left:right]=a[left:right]
    used=set(a[left:right]);values=[i for i in b[right:]+b[:right] if i not in used]
    for j,i in zip(list(range(right,len(a)))+list(range(left)),values):out[j]=i
    return out

def solve(inst,seed=0,population=40,generations=100,objective='fuel_litres',method='ga',volume_buffer=None,cost_overrides=None,local_search=True,crossover_rate=0.9,heuristic_seed=True):
    allowed=validate_instance(inst,volume_buffer);n=len(inst['customers'])-1
    fixed=fixed_type_indices(inst)
    if any(not allowed[i] for i in range(1,n+1)):raise ValueError('An indivisible order fits no vehicle type')
    if objective not in ['fuel_litres','distance','cost'] or method not in ['ga','random'] or population<4 or generations<0:raise ValueError('Invalid search configuration')
    key='distance_km' if objective=='distance' else ('total_eur' if objective=='cost' else 'fuel_litres')
    rng=random.Random(seed);start=time.perf_counter();evaluations=0
    buf=inst.get('model',{}).get('volume_buffer',0.0) if volume_buffer is None else volume_buffer
    def evaluate(g):
        nonlocal evaluations
        evaluations+=1
        try:return decode(g,inst,local_search=local_search,volume_buffer=volume_buffer,cost_overrides=cost_overrides,search_objective=objective)
        except InfeasiblePartition:return {'genome':g,key:math.inf}
    base_order=[i for trip in inst['reference_transports'] for i in trip['customers']]
    base_assign=[None]*n
    for trip in inst['reference_transports']:
        for i in trip['customers']:base_assign[i-1]=trip['vehicle']
    # The witness verifies coverage/capacity, but may not satisfy the newly selected hard stop policy.
    import copy
    witness_inst=copy.deepcopy(inst);witness_inst['model']['stop_count_mode']='soft'
    witness_validation=validate_solution(witness_inst,inst['reference_transports'],volume_buffer=volume_buffer,cost_overrides=cost_overrides)
    type_by_id={v['id']:i for i,v in enumerate(inst['vehicle_types'])}
    base_types=[type_by_id[v['type_id']] for v in inst['vehicles']]
    base=evaluate([base_order,base_assign,base_types]);pool=[base]
    if heuristic_seed:
        nn_order=[];distances=inst['distance_matrix_m']
        for k in range(len(base_types)):
            remaining={i for i in range(1,n+1) if base_assign[i-1]==k};last=0
            while remaining:
                node=min(remaining,key=lambda i:(distances[last][i],i));nn_order.append(node);remaining.remove(node);last=node
        pool.append(evaluate([nn_order,base_assign[:],base_types[:]]))
    def repair(g):
        order,assignment,types=g
        for i in range(1,n+1):
            k=assignment[i-1]
            if 0<=k<len(types) and types[k] in allowed[i]:continue
            slots=[j for j,t in enumerate(types) if t in allowed[i]]
            if not slots:
                if fixed is not None:raise ValueError('An order fits no physical vehicle in the fixed fleet')
                k=rng.randrange(len(types));types[k]=rng.choice(allowed[i]);slots=[k]
            assignment[i-1]=rng.choice(slots)
        return g
    def random_genome():
        types=fixed[:] if fixed is not None else [rng.randrange(len(inst['vehicle_types'])) for _ in range(inst['fleet_size'])]
        # At least one slot must carry every indivisible order.
        if fixed is None and any(not any(t in allowed[i] for t in types) for i in range(1,n+1)):
            hard=max(range(1,n+1),key=lambda i:-len(allowed[i]));types[rng.randrange(len(types))]=rng.choice(allowed[hard])
        return repair([rng.sample(range(1,n+1),n),[rng.randrange(len(types)) for _ in range(n)],types])
    for _ in range(population-len(pool)):pool.append(evaluate(random_genome()))
    pool.sort(key=lambda x:x[key])
    if not math.isfinite(pool[0][key]):
        # A conservative hard-policy seed: try serving all orders with one available
        # compatible vehicle. This is a heuristic, not an infeasibility certificate.
        for k,t in sorted(enumerate(base_types),key=lambda kt:-inst['vehicle_types'][kt[1]]['volume_m3']):
            if not all(t in allowed[i] for i in range(1,n+1)):continue
            candidate=evaluate([base_order[:],[k]*n,base_types[:]])
            if math.isfinite(candidate[key]):
                pool[-1]=candidate;pool.sort(key=lambda x:x[key]);break
        if not math.isfinite(pool[0][key]):raise InfeasiblePartition('Initialization found no hard-feasible candidate; this does not prove the instance infeasible')
    best=pool[0]
    def diagnostic(generation):
        feasible=[p for p in pool if math.isfinite(p[key])]
        signatures={tuple((t['vehicle'],tuple(t['customers'])) for t in p['transports']) for p in feasible}
        return {'generation':generation,'objective':best[key],'evaluations':evaluations,
                'unique_decoded_plans':len(signatures),'feasible_population':len(feasible),'population_size':len(pool)}
    history=[diagnostic(0)]
    for generation in range(1,generations+1):
        next_pool=pool[:2]
        for _ in range(population-2):
            if method=='random':g=random_genome()
            else:
                a=min(rng.sample(pool,3),key=lambda x:x[key])['genome'];b=min(rng.sample(pool,3),key=lambda x:x[key])['genome']
                order=ox(a[0],b[0],rng) if rng.random()<crossover_rate else a[0][:]
                assignment=[aa if rng.random()<.5 else bb for aa,bb in zip(a[1],b[1])]
                if n>1 and rng.random()<.3:
                    i,j=sorted(rng.sample(range(n),2))
                    if rng.random()<.5:order[i],order[j]=order[j],order[i]
                    else:order[i:j+1]=reversed(order[i:j+1])
                if rng.random()<.3:
                    i=rng.randrange(n)
                    if inst['model'].get('stop_count_mode','soft')!='hard' and rng.random()<.5:
                        # Under the priced minimum the repair dissolves single-customer trips, so
                        # half of the soft-mode moves relocate a minimum-size block: the customers
                        # nearest to customer i+1 on its vehicle that fit the target's capacity.
                        lo=soft_min_stops(inst);source=assignment[i];slots=[j for j in range(len(a[2])) if j!=source]
                        if slots:
                            target=rng.choice(slots);vt=inst['vehicle_types'][a[2][target]];vcap=vt['volume_m3']*(1.0-buf)
                            block=[];w=vol=0.
                            for j in sorted((j for j in order if assignment[j-1]==source),key=lambda j:inst['distance_matrix_m'][i+1][j]):
                                cj=inst['customers'][j]
                                if a[2][target] not in allowed[j] or w+cj['weight_kg']>vt['payload_kg']+EPS or vol+cj['volume_m3']>vcap+EPS:continue
                                block.append(j);w+=cj['weight_kg'];vol+=cj['volume_m3']
                                if len(block)==lo:break
                            if len(block)==lo:
                                for c in block:assignment[c-1]=target
                    elif inst['model'].get('stop_count_mode','soft')=='hard':
                        # Single-customer moves cannot activate an empty vehicle with
                        # a hard minimum. Move a minimum-size group instead.
                        lo,_=stop_limits(inst);source=assignment[i]
                        members=[j for j in order if assignment[j-1]==source]
                        if len(members)>=lo:
                            block=rng.sample(members,lo)
                            slots=[j for j,t in enumerate(a[2]) if j!=source and all(t in allowed[c] for c in block)]
                            if slots:
                                target=rng.choice(slots)
                                for c in block:assignment[c-1]=target
                    else:
                        slots=[j for j,t in enumerate(a[2]) if t in allowed[i+1]]
                        if slots:assignment[i]=rng.choice(slots)
                types=fixed[:] if fixed is not None else [aa if rng.random()<.5 else bb for aa,bb in zip(a[2],b[2])]
                if fixed is None and rng.random()<.3:
                    j=rng.randrange(len(types));types[j]=rng.randrange(len(inst['vehicle_types']))
                g=repair([order,assignment,types])
            child=evaluate(g);next_pool.append(child)
        pool=sorted(next_pool,key=lambda x:x[key]);best=min(best,pool[0],key=lambda x:x[key])
        history.append(diagnostic(generation))
    elapsed=time.perf_counter()-start
    return {'instance':inst['name'],'seed':seed,'method':method,'objective':objective,'population':population,
        'heuristic_seed':heuristic_seed,'local_search':local_search,'crossover_rate':crossover_rate,'generations':generations,'evaluations':evaluations,'runtime_seconds':elapsed,
        'best':best,'baseline_decoded':base if math.isfinite(base[key]) else None,'generated_witness':witness_validation,
        'validation':validate_solution(inst,best['transports'],best['fleet'],volume_buffer=volume_buffer,cost_overrides=cost_overrides),'history':history,'stop_count_mode':inst['model'].get('stop_count_mode','soft'),
        'optimality_gap':None,'warning':'No certified optimum. Five available vehicles; idle slots are allowed. Overtime is charged at the configured multiplier. No 3D loading.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--instance',type=Path,default=ROOT/'data/example.json')
    p.add_argument('--objective',choices=['fuel_litres','distance','cost'],default='fuel_litres');p.add_argument('--seed',type=int,default=0)
    p.add_argument('--population',type=int,default=40);p.add_argument('--generations',type=int,default=100)
    p.add_argument('--method',choices=['ga','random'],default='ga');p.add_argument('--output',type=Path,default=ROOT/'results/solution.json')
    p.add_argument('--stop-count-mode',choices=['soft','hard'],default=None);p.add_argument('--require-road',action='store_true');p.add_argument('--volume-buffer',type=float,default=None);p.add_argument('--fuel-price',type=float,default=None)
    p.add_argument('--wage',type=float,default=None);p.add_argument('--overtime-multiplier',type=float,default=None);a=p.parse_args()
    overrides={}
    if a.fuel_price is not None:overrides['fuel_price']=a.fuel_price
    if a.wage is not None:overrides['wage']=a.wage
    if a.overtime_multiplier is not None:overrides['overtime_mult']=a.overtime_multiplier
    inst=json.loads(a.instance.read_text())
    if a.stop_count_mode:inst['model']['stop_count_mode']=a.stop_count_mode
    if a.require_road and ('road_network' not in inst or 'duration_matrix_s' not in inst):raise ValueError('Road matrices and provenance are required')
    result=solve(inst,a.seed,a.population,a.generations,a.objective,a.method,volume_buffer=a.volume_buffer,cost_overrides=overrides)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:result[k] for k in ['instance','method','objective','runtime_seconds','evaluations']},indent=2))
    print(json.dumps({k:v for k,v in result['validation'].items() if k!='trip_details'},indent=2))

if __name__=='__main__':main()

