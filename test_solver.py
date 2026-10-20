import copy,itertools,json,math,unittest
from pathlib import Path
from solver import decode,make_fleet,route_m,schedule,solve,split_vehicle,validate_instance,validate_solution

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

if __name__=='__main__':unittest.main()
