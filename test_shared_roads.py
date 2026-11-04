import copy
import json
import tempfile
import unittest
from pathlib import Path

from build_shared_roads import attach, bounds, coordinates, local_matrices
from solver import schedule
from test_solver import ready


class SharedRoadTests(unittest.TestCase):
    def graph(self):
        return {'elements': [
            *[{'type': 'node', 'id': i, 'lon': 19 + dx, 'lat': 47 + dy}
              for i, dx, dy in [(1, 0, 0), (2, .001, 0), (3, .001, .001),
                                (4, 0, .001), (5, .00002, .00002), (6, .00003, .00002)]],
            {'type': 'way', 'id': 10, 'nodes': [1, 2, 3, 4, 1],
             'tags': {'highway': 'residential', 'oneway': 'yes'}},
            {'type': 'way', 'id': 11, 'nodes': [5, 6], 'tags': {'highway': 'service'}}]}

    def test_directed_paths_preserve_customer_locations_and_parameters(self):
        x = ready()
        x['coordinates_lonlat'] = [[19, 47], [19.001, 47], [19.001, 47.001], [19, 47.001], [19.001, 47]]
        x['reference_transports'] = schedule([[], [], [[1, 2, 3, 4]], [], []], x)
        original = copy.deepcopy(x)
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td)/'roads.json'
            raw.write_text(json.dumps(self.graph()))
            d, t, info, ids = local_matrices(coordinates(x), raw)
        y = attach(x, d, t, info, ids)
        self.assertEqual(x, original)
        for field in ['customers', 'vehicles', 'vehicle_types', 'model', 'coordinates_lonlat']:
            self.assertEqual(y[field], original[field])
        self.assertGreater(d[1][0], d[0][1])
        self.assertAlmostEqual(t[0][1], d[0][1]/25*3.6)
        self.assertEqual([d[i][i] for i in range(5)], [0]*5)
        self.assertEqual(ids[1], ids[4])  # colocated addresses remain distinct customers
        self.assertEqual(len(y['customers']), 5)

    def test_unreachable_vertex_is_not_silently_replaced(self):
        coords = [[19, 47], [19.00002, 47.00002]]
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td)/'roads.json'
            raw.write_text(json.dumps(self.graph()))
            with self.assertRaisesRegex(ValueError, 'not mutually reachable'):
                local_matrices(coords, raw)
            _, _, info, ids = local_matrices(coords, raw, snap_to_depot_component=True)
            self.assertEqual(info['component_resnaps'][0]['customer_id'], 1)
            self.assertEqual(info['component_resnaps'][0]['nearest_vertex'], 5)
            self.assertEqual(ids, [1, 1])

    def test_far_address_fails_instead_of_fabricating_a_road(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td)/'roads.json'
            raw.write_text(json.dumps(self.graph()))
            with self.assertRaisesRegex(ValueError, 'maximum'):
                local_matrices([[19, 47], [20, 48]], raw, max_snap_m=50)

    def test_missing_invalid_or_reordered_coordinate_shape_rejected(self):
        x = ready()
        with self.assertRaises(ValueError):
            coordinates(x)
        for value in [[], [[19, 47]]*4, [[19, float('nan')]]*5, [[47, 190]]*5, [[True, 47]]*5]:
            x['coordinates_lonlat'] = value
            with self.assertRaises(ValueError):
                coordinates(x)

    def test_extent_covers_every_original_point_with_margin(self):
        self.assertEqual(bounds([[19, 47], [20, 48]], .1), [18.9, 46.9, 20.1, 48.1])

    def test_map_geometry_obeys_oneway_instead_of_connecting_stops_directly(self):
        from budapest_osm import graph_from_osm
        from map_shared_routes import path_to_targets
        _, graph = graph_from_osm(self.graph())
        self.assertEqual(path_to_targets(graph, 1, {1, 4}), {1: [1], 4: [1, 2, 3, 4]})


if __name__ == '__main__':
    unittest.main()
