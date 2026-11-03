"""Convert the PSO team's CSV dataset (xsilentkiller/industrial-transport) into
our schema-v3 instance JSON so both teams optimise the same benchmark.

    python import_pso_dataset.py --source <clone of the PSO team repo> --output data/shared_pso_250.json

Mapping (PSO team field -> ours):
  orders.csv      total_weight_kg->weight_kg, total_volume_m3->volume_m3,
                  packing_time_min + loading_time_min -> service_minutes
                  (params.loading_counts_as_work_time is true), item_ids -> items[]
  locations.csv   lat/lon -> coordinates_km (equirectangular, depot at origin)
  distances.csv   km -> distance_matrix_m (PSO team haversine x 1.3 winding factor)
  vehicles.csv    max_weight_kg->payload_kg, max_volume_m3->volume_m3,
                  fuel_l_per_km*100->fuel_l_per_100km, avg_speed_kmh->speed_kmh,
                  wage_per_h->wage_eur_per_h, maintenance_per_1000km->maintenance_eur_per_1000km
  params.json     shift_hours, overtime_multiplier, fuel_price_per_l->fuel_price_eur_per_l,
                  required_free_volume_ratio->volume_buffer, min/max_customers_per_trip
  best_solution   PSO team published plan -> pso_reference_solution (evaluator cross-check ONLY)
reference_transports (the solver's neutral starting plan) is a nearest-neighbour
tour cut greedily by capacity, so neither team starts from the other's result.
Standard library only.
"""
import argparse,csv,json,math,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def convert(source,solver_dir=ROOT,name='Shared-PSO-250-Budapest'):
    src=Path(source);ds=src/'dataset'
    params=json.loads((ds/'params.json').read_text())
    furniture={r['id']:r for r in read_csv(ds/'furniture_clean.csv')}
    locations={int(r['location_id']):r for r in read_csv(ds/'locations.csv')}
    orders=sorted(read_csv(ds/'orders.csv'),key=lambda r:int(r['location_id']))
    vrows=read_csv(ds/'vehicles.csv')
    n=len(orders)
    if [int(r['location_id']) for r in orders]!=list(range(1,n+1)):raise ValueError('orders must map 1:1 onto customer ids 1..n')
    if params.get('depot_id',0)!=0 or locations[0]['type']!='depot':raise ValueError('expected depot at location 0')

    # customers: 0 = depot
    customers=[{'id':0,'weight_kg':0.,'volume_m3':0.,'service_minutes':0.,'items':[]}]
    for r in orders:
        items=[]
        for fid in r['item_ids'].split(';'):
            f=furniture[fid];dims=[float(f['length_m']),float(f['width_m']),float(f['height_m'])]
            items.append({'catalog_id':fid,'name':f['name'],'weight_kg':float(f['weight_kg']),'volume_m3':math.prod(dims),
                          'dimensions_m':dims,'dimension_basis':'pso_team_furniture_clean','weight_basis':'pso_team_furniture_clean'})
        service=float(r['packing_time_min'])+(float(r['loading_time_min']) if params.get('loading_counts_as_work_time',True) else 0.)
        customers.append({'id':int(r['location_id']),'weight_kg':float(r['total_weight_kg']),'volume_m3':float(r['total_volume_m3']),
                          'service_minutes':round(service,4),'items':items,
                          'loading_minutes':float(r['loading_time_min']),'unloading_minutes':float(r['packing_time_min']),
                          'address':locations[int(r['location_id'])]['full_address']})

    # coordinates: equirectangular projection in km, depot at origin
    lat0,lon0=float(locations[0]['lat']),float(locations[0]['lon']);kx=111.32*math.cos(math.radians(lat0));ky=110.57
    coords=[[round((float(locations[i]['lon'])-lon0)*kx,4),round((float(locations[i]['lat'])-lat0)*ky,4)] for i in range(n+1)]
    lonlat=[[float(locations[i]['lon']),float(locations[i]['lat'])] for i in range(n+1)]

    # distance matrix: km -> integer metres
    rows=read_csv(ds/'distances.csv')
    if len(rows)!=n+1:raise ValueError('distance matrix size mismatch')
    d=[[int(round(float(rows[i][str(j)])*1000)) for j in range(n+1)] for i in range(n+1)]

    # vehicle types and the fixed fleet (same order as the PSO team vehicle_id)
    types=[];type_index={}
    for r in vrows:
        t=r['type_id']
        if t not in type_index:
            type_index[t]=len(types)
            types.append({'id':t,'name':r['model'],'volume_m3':float(r['max_volume_m3']),'payload_kg':float(r['max_weight_kg']),
                          'cargo_length_m':float(r['cargo_length_m']),'cargo_width_m':float(r['cargo_width_m']),'cargo_height_m':float(r['cargo_height_m']),
                          'fuel_l_per_100km':round(float(r['fuel_l_per_km'])*100,4),'top_speed_kmh':float(r['top_speed_kmh']),
                          'speed_kmh':float(r['avg_speed_kmh']),'wage_eur_per_h':float(r['wage_per_h']),
                          'maintenance_eur_per_1000km':float(r['maintenance_per_1000km']),
                          'source':'PSO team vehicles.csv (xsilentkiller/industrial-transport); cargo dims, speeds, wages, maintenance marked assumed there'})
    witness_types=[type_index[r['type_id']] for r in vrows]
    vehicles=[dict(types[t],id=f'{types[t]["id"]}-{k+1}',type_id=types[t]['id']) for k,t in enumerate(witness_types)]
    # the current solver schedules every vehicle at model.schedule_average_speed_kmh
    fleet_speed=sum(v['speed_kmh'] for v in vehicles)/len(vehicles)

    inst={'schema_version':3,'name':name,'seed':42,'cycles_per_vehicle':None,'fleet_size':len(vehicles),
          'vehicle_types':types,'vehicles':vehicles,'customers':customers,'coordinates_km':coords,'coordinates_lonlat':lonlat,'distance_matrix_m':d,
          'reference_transports':[],
          'provenance':{'source':'https://github.com/xsilentkiller/industrial-transport dataset/ (PSO team), seed 42',
                        'locations':'real Budapest addresses from OpenStreetMap Overpass; depot 47.405N 19.11E (district 23)',
                        'distances':'haversine x 1.3 winding factor, km rounded to 3 decimals (not road routing)',
                        'furniture':'furniture_clean.csv (Amazon listing scrape, inches->m); order volume = sum of item bounding boxes',
                        'service_minutes':'packing_time_min + loading_time_min because loading_counts_as_work_time=true',
                        'schedule_speed':f'model.schedule_average_speed_kmh = fleet mean {fleet_speed:.2f}; per-vehicle avg_speed_kmh kept in vehicles[].speed_kmh',
                        'warning':'Vehicle wages, speeds, maintenance and cargo dimensions are the PSO team\'s stated assumptions.'},
          'model':{'depot':0,'fleet_mix_is_decision':False,'multiple_sequential_trips':bool(params.get('allow_multiple_trips_per_vehicle',True)),
                   'all_orders_available_at_time_zero':True,'time_horizon_minutes':None,'objective':'cost',
                   'schedule_average_speed_kmh':round(fleet_speed,4),
                   'shift_hours':float(params['shift_hours']),'overtime_multiplier':float(params['overtime_multiplier']),
                   'fuel_price_eur_per_l':float(params['fuel_price_per_l']),'volume_buffer':float(params['required_free_volume_ratio']),
                   'min_stops_per_trip':int(params['min_customers_per_trip']),'max_stops_per_trip':int(params['max_customers_per_trip']),
                   'min_stops_penalty_eur_per_customer':2000.0,'loading_counts_as_work_time':bool(params.get('loading_counts_as_work_time',True)),
                   'packing_mode':int(params.get('packing_mode',1)),
                   'not_implemented':['3D packing','time windows','release times','road network','load-dependent fuel'],
                   'cost_parameters_are_assumptions':True}}

    # neutral starting plan: nearest-neighbour tour, cut greedily by payload / buffered volume / max stops,
    # trips handed to the fixed fleet in turn (a vehicle that gets several trips drives them one after another)
    sys.path.insert(0,str(solver_dir));import solver
    buf=inst['model']['volume_buffer'];max_stops=inst['model']['max_stops_per_trip']
    unvisited=set(range(1,n+1));cur=0;order=[]
    while unvisited:
        cur=min(unvisited,key=lambda j:d[cur][j]);order.append(cur);unvisited.remove(cur)
    groups=[[] for _ in vehicles];i=k=0;empties=0
    while i<n:
        v=vehicles[k%len(vehicles)];w=vol=0.;trip=[]
        while i<n and len(trip)<max_stops:
            c=customers[order[i]]
            if w+c['weight_kg']>v['payload_kg'] or vol+c['volume_m3']>v['volume_m3']*(1-buf):break
            trip.append(order[i]);w+=c['weight_kg'];vol+=c['volume_m3'];i+=1
        k+=1
        if not trip:
            empties+=1
            if empties>=len(vehicles):raise ValueError(f'customer {order[i]} fits no vehicle under the volume buffer')
            continue
        empties=0;groups[(k-1)%len(vehicles)].append(trip)
    inst['reference_transports']=solver.schedule(groups,inst,vehicles)
    inst['provenance']['reference_transports']='nearest-neighbour tour, greedy capacity split, round-robin fleet; neutral start for both teams'

    # PSO team published plan, kept only to cross-check that both evaluators agree
    best=json.loads((src/'output/best_solution.json').read_text())['best_solution']
    pso_groups=[[] for _ in vehicles]
    for t in best['trips']:pso_groups[t['vehicle_index']].append([int(c) for c in t['customers']])
    inst['pso_reference_solution']={'method':best['method'],'true_cost_eur_reported':best['true_cost_eur'],'n_trips':best['n_trips'],
        'transports':solver.schedule(pso_groups,inst,vehicles),'note':'PSO team result for evaluator cross-check only; never used for initialisation'}
    allowed=solver.validate_instance(inst)
    if any(not allowed[i] for i in range(1,n+1)):raise ValueError('an order fits no vehicle under the volume buffer')
    check=solver.validate_solution(inst,inst['reference_transports'])
    pso_check=solver.validate_solution(inst,inst['pso_reference_solution']['transports'])
    inst['pso_reference_solution']['true_cost_eur_ours']=pso_check['cost']['real_cost_eur']
    return inst,check,pso_check

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--source',type=Path,required=True,help='clone of xsilentkiller/industrial-transport')
    p.add_argument('--output',type=Path,default=ROOT/'data/shared_pso_250.json')
    p.add_argument('--solver-dir',type=Path,default=ROOT);a=p.parse_args()
    inst,check,pso_check=convert(a.source,a.solver_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(inst,indent=1,allow_nan=False),encoding='utf-8')
    print(json.dumps({'instance':inst['name'],'customers':len(inst['customers'])-1,'vehicles':[v['id'] for v in inst['vehicles']],
                      'neutral_witness':{'trips':check['trips'],'real_cost_eur':check['cost']['real_cost_eur'],'penalty_eur':check['cost']['penalty_eur'],'total_eur':check['cost']['total_eur'],'below_min':check['cost']['trips_below_min']},
                      'pso_plan_check':{'reported_true_cost_eur':inst['pso_reference_solution']['true_cost_eur_reported'],'ours_real_cost_eur':pso_check['cost']['real_cost_eur'],'ours_penalty_eur':pso_check['cost']['penalty_eur'],'ours_total_eur':pso_check['cost']['total_eur']},
                      'output':str(a.output)},indent=1))

if __name__=='__main__':main()
