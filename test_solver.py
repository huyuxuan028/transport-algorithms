import copy,itertools,json,math,unittest
from pathlib import Path
from solver import decode,evaluate_costs,make_fleet,route_m,schedule,solve,split_vehicle,validate_instance,validate_solution

ROOT=Path(__file__).parent

def tiny():
    d=[[0,2,4,3,6],[2,0,2,3,5],[4,2,0,2,3],[3,3,2,0,4],[6,5,3,4,0]]
    return {'name':'tiny','distance_matrix_m':d,
        'vehicle_types':[{'id':'small','payload_kg':5,'volume_m3':5,'fuel_l_per_100km':5},
                         {'id':'medium','payload_kg':7,'volume_m3':7,'fuel_l_per_100km':8},
                         {'id':'large','payload_kg':10,'volume_m3':10,'fuel_l_per_100km':12}],
        'fleet_size':5,
        'customers':[{'id':i,'weight_kg':w,'volume_m3':v,'service_minutes':0,'items':[]} for i,(w,v) in enumerate([(0,0),(2,1),(3,3),(1,3),(4,2)])],
        'model':{'schedule_average_speed_kmh':30},'reference_transports':[]}

def ready():
    x=tiny();x['vehicles']=make_fleet(x,[0,1,2,0,1]);return x

class Tests(unittest.TestCase):
    def test_split_matches_exhaustive_contiguous_partitions(self):
        x=ready();v=x['vehicles'][0]
        for order in itertools.permutations(range(1,5)):
            values=[]
            for cuts in itertools.product([0,1],repeat=3):
                groups=[];start=0
                for j,cut in enumerate(cuts,1):
                    if cut:groups.append(list(order[start:j]));start=j
                groups.append(list(order[start:]))
                if all(sum(x['customers'][i]['weight_kg'] for i in g)<=5 and sum(x['customers'][i]['volume_m3'] for i in g)<=5 for g in groups):
                    values.append(sum(route_m(g,x['distance_matrix_m']) for g in groups))
            output=split_vehicle(list(order),v,x)
            self.assertEqual(sum(route_m(g,x['distance_matrix_m']) for g in output),min(values))
    def test_allocation_is_indexed_by_customer_not_permutation_position(self):
        x=ready();out=decode([[3,1,4,2],[0,1,0,1],[0,1,2,0,1]],x)
        got={i:t['vehicle'] for t in out['transports'] for i in t['customers']}
        self.assertEqual(got,{1:0,2:1,3:0,4:1})
    def test_validator_rejects_coverage_overload_and_nan(self):
        x=ready();out=decode([[1,2,3,4],[0,0,0,0],[0,1,2,0,1]],x)
        for error in ['missing','overload','nan']:
            trips=copy.deepcopy(out['transports'])
            if error=='missing':trips=trips[1:]
            elif error=='overload':trips=schedule([[[1,2,3,4]],[],[],[],[]],x)
            else:trips[0]['finish_minutes']=float('nan')
            with self.assertRaises(ValueError):validate_solution(x,trips)
    def test_multi_trip_schedule_rejects_overlap(self):
        x=ready();trips=schedule([[[1,2],[3,4]],[],[],[],[]],x)
        self.assertTrue(validate_solution(x,trips)['feasible'])
        trips[1]['start_minutes']=0
        with self.assertRaises(ValueError):validate_solution(x,trips)
    def test_catalog_items_match_aggregated_customer_demands(self):
        x=json.loads((ROOT/'data/example.json').read_text())
        for c in x['customers'][1:]:
            self.assertAlmostEqual(c['weight_kg'],sum(i['weight_kg'] for i in c['items']))
            self.assertAlmostEqual(c['volume_m3'],sum(math.prod(i['dimensions_m']) for i in c['items']))
        self.assertTrue(validate_solution(x,x['reference_transports'])['feasible'])
    def test_search_is_feasible_and_elitist(self):
        x=ready();x['reference_transports']=schedule([[[1,2],[3,4]],[],[],[],[]],x)
        out=solve(x,0,12,8)
        self.assertTrue(out['validation']['feasible'])
        self.assertLessEqual(out['best']['fuel_litres'],out['history'][0]['objective'])
        self.assertEqual(len(out['best']['fleet']),5)
    def test_fleet_type_controls_capacity_and_fuel(self):
        x=ready();g=[[1,2,3,4],[0,0,0,0],[0,1,2,0,1]]
        a=decode(g,x);b=decode([g[0],g[1],[2,1,2,0,1]],x)
        self.assertGreater(b['fuel_litres'],a['fuel_litres'])
        self.assertEqual(validate_solution(x,b['transports'],b['fleet'])['fleet_type_ids'][0],'large')
        with self.assertRaises(ValueError):decode([[1,2,3,4],[0,0,0,0],[0,1]],x)
    def test_large_order_requires_a_compatible_type_after_fleet_evolution(self):
        x=ready();x['customers'][4]['volume_m3']=9
        x['reference_transports']=schedule([[[1,2],[3]],[],[[4]],[],[]],x)
        out=solve(x,seed=7,population=12,generations=8)
        self.assertEqual(len(out['best']['fleet']),5)
        self.assertIn('large',out['validation']['fleet_type_ids'])
        self.assertTrue(out['validation']['feasible'])

    def test_wage_without_overtime_and_with_overtime(self):
        x=ready();vehicles=x['vehicles']
        trips_regular=[{'vehicle':0,'customers':[1,2],'start_minutes':0,'finish_minutes':360,'distance_km':100,'fuel_litres':10}]
        c_reg=evaluate_costs(trips_regular,vehicles,x)
        self.assertAlmostEqual(c_reg['wage_eur'],120.0);self.assertAlmostEqual(c_reg['overtime_hours'],0.0)
        trips_ot=[{'vehicle':0,'customers':[1,2],'start_minutes':0,'finish_minutes':600,'distance_km':100,'fuel_litres':10}]
        c_ot=evaluate_costs(trips_ot,vehicles,x)
        self.assertAlmostEqual(c_ot['wage_eur'],240.0);self.assertAlmostEqual(c_ot['overtime_hours'],2.0)
    def test_maintenance_cost_scaling(self):
        x=ready();vehicles=x['vehicles']
        trips=[{'vehicle':0,'customers':[1],'start_minutes':0,'finish_minutes':60,'distance_km':1000,'fuel_litres':10}]
        c=evaluate_costs(trips,vehicles,x)
        self.assertAlmostEqual(c['maintenance_eur'],80.0)
    def test_solver_repair_respects_instance_volume_buffer(self):
        x=ready();x['model']['volume_buffer']=0.10
        x['customers'][1]['volume_m3']=4.6
        x['vehicles']=make_fleet(x,[2,2,2,2,2])
        x['reference_transports']=schedule([[[1],[2],[3],[4]],[],[],[],[]],x)
        allowed=validate_instance(x)
        self.assertNotIn(0,allowed[1])
        out=solve(x,seed=3,population=8,generations=2)
        self.assertTrue(out['validation']['feasible'])
        self.assertGreaterEqual(out['best']['fleet'][out['best']['genome'][1][0]]['volume_m3'],4.6/0.9)

    def test_instance_cost_parameters_and_explicit_overrides(self):
        x=ready();x['model'].update({'fuel_price_eur_per_l':1.60,'overtime_multiplier':3.0,
            'shift_hours':6.0,'min_stops_per_trip':3,'max_stops_per_trip':1})
        trips=[{'vehicle':0,'customers':[1,2],'start_minutes':0,'finish_minutes':600,'distance_km':100,'fuel_litres':10}]
        cost=evaluate_costs(trips,x['vehicles'],x)
        self.assertAlmostEqual(cost['fuel_eur'],16.0)
        self.assertAlmostEqual(cost['wage_eur'],360.0)
        self.assertAlmostEqual(cost['overtime_hours'],4.0)
        self.assertEqual(cost['trips_below_min'],1);self.assertEqual(cost['trips_above_max'],1)
        overridden=evaluate_costs(trips,x['vehicles'],x,{'fuel_price':2.0,'overtime_mult':4.0,
            'shift_h':8.0,'min_stops':1,'max_stops':3})
        self.assertAlmostEqual(overridden['fuel_eur'],20.0)
        self.assertAlmostEqual(overridden['wage_eur'],320.0)
        self.assertEqual(overridden['trips_below_min'],0);self.assertEqual(overridden['trips_above_max'],0)

    def test_volume_buffer_reduces_usable_capacity(self):
        x=ready();v={'payload_kg':10,'volume_m3':10,'fuel_l_per_100km':5}
        x['customers'][1]['volume_m3']=9.5;x['customers'][2]['volume_m3']=0.1
        self.assertEqual(len(split_vehicle([1],v,x,volume_buffer=0.0)),1)
        with self.assertRaises(ValueError):split_vehicle([1],v,x,volume_buffer=0.10)
    def test_trip_size_audit_counts(self):
        x=ready();vehicles=x['vehicles']
        trips=[{'vehicle':0,'customers':[1,2],'start_minutes':0,'finish_minutes':60,'distance_km':10,'fuel_litres':1}]
        c=evaluate_costs(trips,vehicles,x)
        self.assertEqual(c['trips_below_min'],1);self.assertEqual(c['trips_above_max'],0)

if __name__=='__main__':unittest.main()
