import hashlib,json,random,re,unittest
from pathlib import Path
from budapest_osm import graph_from_osm,shortest
from solver import validate_solution
ROOT=Path(__file__).parent
class BudapestIntegration(unittest.TestCase):
    def test_frozen_road_matrices_match_source_and_orders_unchanged(self):
        x=json.loads((ROOT/'data/budapest_road.json').read_text());source=json.loads((ROOT/'data/benchmark_250.json').read_text());raw=ROOT/'data/budapest_osm_raw.json'
        self.assertEqual(x['customers'],source['customers']);self.assertEqual(x['vehicles'],source['vehicles']);self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),x['road_network']['raw_sha256'])
        _,g=graph_from_osm(json.loads(raw.read_text()));ids=x['osm_node_ids']
        for i in [0,5,100,250]:
            d,t,_=shortest(g,ids[i])
            for j in range(len(ids)):
                self.assertAlmostEqual(x['distance_matrix_m'][i][j],d[ids[j]]);self.assertAlmostEqual(x['duration_matrix_s'][i][j],t[ids[j]])
        self.assertTrue(any(abs(x['distance_matrix_m'][i][j]-x['distance_matrix_m'][j][i])>1 for i in range(len(ids)) for j in range(len(ids))))
    def test_map_embeds_json_geometry_not_straight_customer_links(self):
        from map_budapest import render
        import tempfile
        x=json.loads((ROOT/'data/budapest_road.json').read_text());r=json.loads((ROOT/'results/budapest_solution.json').read_text())
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'map.html';render(x,r,ROOT/'data/budapest_osm_raw.json',out);s=out.read_text();data=json.loads(re.search(r'const d=(.*?);const el=',s,re.S).group(1))
            self.assertEqual(len(data['routes']),len(r['best']['transports']));self.assertTrue(any(len(a['points'])>len(b['customers'])+2 for a,b in zip(data['routes'],r['best']['transports'])))
            self.assertIn('OpenStreetMap contributors',s)
if __name__=='__main__':unittest.main()
