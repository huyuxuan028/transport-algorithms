import copy,tempfile,unittest
import random
from solver import route_m,two_opt,schedule,validate_instance,validate_solution
from road_network import build_matrices
from test_solver import ready
class RoadTests(unittest.TestCase):
    def test_directed_two_opt_never_worsens_internal_arcs(self):
        d=[[0,1,9,9],[9,0,1,1],[1,50,0,1],[1,1,50,0]]
        r=[1,2,3]
        self.assertLessEqual(route_m(two_opt(r,d),d),route_m(r,d))
    def test_directed_two_opt_matches_exhaustive_one_move(self):
        rng=random.Random(42)
        for _ in range(30):
            d=[[0 if i==j else rng.randint(1,50) for j in range(6)] for i in range(6)]
            r=[1,2,3,4,5];candidates=[r]
            for i in range(4):
                for j in range(i+1,5):candidates.append(r[:i]+list(reversed(r[i:j+1]))+r[j+1:])
            self.assertEqual(route_m(two_opt(r,d),d),min(route_m(v,d) for v in candidates))
    def test_schedule_uses_road_seconds_and_validator_agrees(self):
        x=ready();n=len(x['customers']);x['duration_matrix_s']=[[0 if i==j else 600 for j in range(n)] for i in range(n)]
        x['distance_matrix_m'][0][1]=7
        validate_instance(x)
        trips=schedule([[],[],[[1,2,3,4]],[],[]],x)
        self.assertEqual(trips[0]['finish_minutes'],50)
        self.assertTrue(validate_solution(x,trips)['feasible'])
        x['duration_matrix_s'][0][1]=None
        with self.assertRaises(ValueError):validate_instance(x)
    def test_batched_directed_matrices_cached_and_null_rejected(self):
        coords=[[19+i*.001,47] for i in range(5)];calls=[]
        def fake(p):
            calls.append(p)
            ids=[round((pt[0]-19)*1000) for pt in p['locations']]
            values=[[0 if ids[i]==ids[j] else 100*ids[i]+ids[j]+1 for j in p['destinations']] for i in p['sources']]
            return {'distances':values,'durations':values}
        with tempfile.TemporaryDirectory() as td:
            d,t=build_matrices(coords,None,td,block=2,request=fake)
            self.assertEqual(len(calls),9);self.assertEqual(d[4][1],402);self.assertEqual(d[1][4],105)
            build_matrices(coords,None,td,block=2,request=lambda _:self.fail('Cache missed'))
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):build_matrices(coords,None,td,request=lambda p:{'distances':[[None]*5 for _ in range(5)],'durations':[[0]*5 for _ in range(5)]})
if __name__=='__main__':unittest.main()
