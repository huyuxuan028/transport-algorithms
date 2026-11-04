import copy,json,tempfile,unittest
from pathlib import Path
from solver import InfeasiblePartition,decode,make_fleet,schedule,solve,split_vehicle,validate_instance,validate_solution,two_opt
from test_solver import ready
from budapest_osm import component,graph_from_osm,shortest
class UpgradeTests(unittest.TestCase):
    def strict(self):
        x=ready();x['model'].update(stop_count_mode='hard',min_stops_per_trip=2,max_stops_per_trip=2)
        x['reference_transports']=schedule([[],[],[[1,2],[3,4]],[],[]],x)
        return x
    def test_hard_split_and_independent_validator(self):
        x=self.strict();self.assertEqual(list(map(len,split_vehicle([1,2,3,4],x['vehicles'][2],x))),[2,2])
        trips=schedule([[],[],[[1],[2,3,4]],[],[]],x)
        with self.assertRaises(ValueError):validate_solution(x,trips)
        with self.assertRaises(InfeasiblePartition):split_vehicle([1,2,3],x['vehicles'][2],x)
    def test_hard_ga_returns_only_hard_feasible_trips(self):
        x=self.strict();r=solve(x,seed=7,population=8,generations=6,objective='cost')
        self.assertTrue(r['validation']['feasible']);self.assertTrue(all(len(t['customers'])==2 for t in r['best']['transports']))
    def test_invalid_buffer_and_policy_rejected(self):
        x=ready()
        for b in [-.1,1,float('nan')]:
            with self.assertRaises(ValueError):validate_instance(x,b)
        x['model']['stop_count_mode']='mystery'
        with self.assertRaises(ValueError):validate_instance(x)
    def test_cost_local_search_never_worsens_decoded_vehicle_cost(self):
        x=ready();n=5;x['duration_matrix_s']=[[0 if i==j else 600 for j in range(n)] for i in range(n)]
        order=[1,3,2,4];candidate=two_opt(order,x['distance_matrix_m'])
        old=set(zip([0]+order,order+[0]));new=set(zip([0]+candidate,candidate+[0]))
        for u,v in new-old:x['duration_matrix_s'][u][v]=100000
        genome=[order,[2]*4,[0,1,2,0,1]]
        a=decode(genome,x,local_search=False,search_objective='cost');b=decode(genome,x,local_search=True,search_objective='cost')
        self.assertLessEqual(b['total_eur'],a['total_eur'])
    def test_osm_oneways_private_roads_and_shortest_paths(self):
        elements=[{'type':'node','id':i,'lon':19+i*.001,'lat':47.5} for i in range(1,5)]
        elements.extend([{'type':'way','id':10,'nodes':[1,2,3],'tags':{'highway':'residential','oneway':'yes'}},{'type':'way','id':11,'nodes':[3,1],'tags':{'highway':'residential','oneway':'yes'}},{'type':'way','id':12,'nodes':[1,4],'tags':{'highway':'residential','access':'private'}}])
        _,g=graph_from_osm({'elements':elements});self.assertNotIn(4,g);self.assertEqual(component(g,1),{1,2,3})
        d,t,p=shortest(g,2);self.assertEqual(p[1],3);self.assertGreater(d[1],0)
if __name__=='__main__':unittest.main()
