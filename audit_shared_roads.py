"""Check shared-data preservation and independently recompute sampled graph rows."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from budapest_osm import graph_from_osm, shortest
from solver import validate_instance


def audit(source, road, raw):
    original = json.loads(Path(source).read_text())
    x = json.loads(Path(road).read_text())
    info = x['road_network']
    if hashlib.sha256(Path(source).read_bytes()).hexdigest() != info['input_sha256']:
        raise ValueError('Shared input hash mismatch')
    if hashlib.sha256(Path(raw).read_bytes()).hexdigest() != info['raw_sha256']:
        raise ValueError('Raw graph hash mismatch')
    for field in ['customers', 'vehicles', 'vehicle_types', 'coordinates_lonlat', 'model']:
        if x[field] != original[field]:
            raise ValueError('Shared field changed: '+field)
    validate_instance(x)
    _, graph = graph_from_osm(json.loads(Path(raw).read_text()))
    ids = x['osm_node_ids']
    for i in sorted(set([0, len(ids)//4, len(ids)//2, 3*len(ids)//4, len(ids)-1])):
        d, t, _ = shortest(graph, ids[i])
        for j, node in enumerate(ids):
            if (not math.isclose(x['distance_matrix_m'][i][j], d[node], abs_tol=1e-7) or
                    not math.isclose(x['duration_matrix_s'][i][j], t[node], abs_tol=1e-7)):
                raise ValueError(f'Path/matrix mismatch {i}->{j}')
    return {'customers': len(ids)-1, 'matrix_shape': [len(ids), len(ids)],
            'fields_preserved': True, 'sampled_rows_recomputed': 5,
            'asymmetric_distance_pairs': sum(abs(x['distance_matrix_m'][i][j]-x['distance_matrix_m'][j][i]) > 1
                                             for i in range(len(ids)) for j in range(i)),
            'road_sha256': hashlib.sha256(Path(road).read_bytes()).hexdigest(),
            'graph_sha256': info['raw_sha256'], 'maximum_snap_m': info['max_snap_distance_m'],
            'component_resnaps': info['component_resnaps']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=Path('data/shared_pso_250.json'))
    p.add_argument('--road', type=Path, default=Path('data/shared_pso_250_road.json'))
    p.add_argument('--raw', type=Path, default=Path('cache/budapest_city_osm.json'))
    a = p.parse_args()
    print(json.dumps(audit(a.source, a.road, a.raw), indent=2))


if __name__ == '__main__':
    main()
