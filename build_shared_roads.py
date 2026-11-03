"""Build directed road matrices for the unchanged shared PSO-team instance.

Local OSM mode uses one cached highway extract covering all original coordinates.
ORS mode uses the same coordinates and requires ORS_API_KEY in the environment.
No synthetic-location or straight-line distance fallback is permitted.
"""
import argparse
import copy
import datetime
import hashlib
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

from budapest_osm import CLASSES, component, graph_from_osm, metres, shortest
from solver import schedule, validate_instance, validate_solution

OVERPASS = 'https://overpass-api.de/api/interpreter'


def coordinates(instance):
    coords = instance.get('coordinates_lonlat')
    if not isinstance(coords, list) or len(coords) != len(instance['customers']):
        raise ValueError('coordinates_lonlat must contain every customer and depot, in ID order')
    for p in coords:
        if (not isinstance(p, list) or len(p) != 2 or
                any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in p) or
                not -180 <= p[0] <= 180 or not -90 <= p[1] <= 90):
            raise ValueError('Expected finite [longitude, latitude] coordinates')
    return coords


def bounds(coords, padding=.04):
    if not math.isfinite(padding) or padding <= 0:
        raise ValueError('Padding must be positive')
    return [min(p[0] for p in coords)-padding, min(p[1] for p in coords)-padding,
            max(p[0] for p in coords)+padding, max(p[1] for p in coords)+padding]


def download_osm(coords, path, padding=.04):
    """One bounded raw-data request, not map tiles. Cached and never retried in a loop."""
    bbox = bounds(coords, padding)
    w, s, e, n = bbox
    query = ('[out:json][timeout:90];way[highway~"^(' + '|'.join(CLASSES) +
             f')$"]({s},{w},{n},{e});(._;>;);out body;')
    url = OVERPASS + '?' + urllib.parse.urlencode({'data': query})
    request = urllib.request.Request(url, headers={
        'User-Agent': 'FurnitureTransportCourse/1.1 (single cached academic road extract)'})
    with urllib.request.urlopen(request, timeout=110) as response:
        body = response.read()
    data = json.loads(body)
    if data.get('remark') or not data.get('elements'):
        raise ValueError('Incomplete/empty Overpass extract: ' + str(data.get('remark', '')))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_bytes(body)
    temp.replace(path)
    path.with_suffix('.source.json').write_text(json.dumps({
        'url': url, 'bbox_wsen': bbox, 'query': query,
        'sha256': hashlib.sha256(body).hexdigest(),
        'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}, indent=2))


def local_matrices(coords, raw, max_snap_m=200, progress=None, snap_to_depot_component=False):
    if not math.isfinite(max_snap_m) or max_snap_m <= 0:
        raise ValueError('Maximum snap distance must be positive')
    data = json.loads(Path(raw).read_text(encoding='utf-8'))
    if data.get('remark'):
        raise ValueError('OSM extract reports an error: ' + str(data['remark']))
    nodes, graph = graph_from_osm(data)
    if not graph:
        raise ValueError('No supported drivable roads')
    # Nearest graph vertex. Keep the address coordinates and audit this approximation.
    # Pre-projecting candidate nodes avoids repeating expensive trig for each pair.
    lat0 = math.radians(sum(p[1] for p in coords)/len(coords))
    sx = math.cos(lat0)
    projected = [(u, nodes[u][0]*sx, nodes[u][1]) for u in graph]
    selected, snap = [], []
    for i, p in enumerate(coords):
        px, py = p[0]*sx, p[1]
        u = min(projected, key=lambda item: ((item[1]-px)**2+(item[2]-py)**2, item[0]))[0]
        gap = metres(p, nodes[u])
        if gap > max_snap_m:
            raise ValueError(f'Location {i} is {gap:.1f}m from nearest road vertex; maximum {max_snap_m}m')
        selected.append(u)
        snap.append(gap)
    connected = component(graph, selected[0])
    missing = [i for i, u in enumerate(selected) if u not in connected]
    resnapped = []
    if missing and snap_to_depot_component:
        reachable = [item for item in projected if item[0] in connected]
        for i in missing:
            p = coords[i]
            px, py = p[0]*sx, p[1]
            u = min(reachable, key=lambda item: ((item[1]-px)**2+(item[2]-py)**2, item[0]))[0]
            gap = metres(p, nodes[u])
            if gap > max_snap_m:
                raise ValueError(f'Location {i}: reachable road vertex is {gap:.1f}m away; maximum {max_snap_m}m')
            resnapped.append({'customer_id': i, 'nearest_vertex': selected[i],
                              'nearest_gap_m': snap[i], 'reachable_vertex': u, 'reachable_gap_m': gap})
            selected[i], snap[i] = u, gap
        missing = []
    if missing:
        raise ValueError(f'Locations not mutually reachable from depot: {missing}; inspect access tags/expand extract')
    distances, durations = [], []
    memo = {}
    for i, u in enumerate(selected):
        if u not in memo:
            d, t, _ = shortest(graph, u)
            memo[u] = ([d[v] for v in selected], [t[v] for v in selected])
        drow, trow = memo[u]
        distances.append(drow[:])
        durations.append(trow[:])
        if progress:
            progress(i+1, len(selected))
    info = {
        'provider': 'local_osm_dijkstra', 'map': 'OpenStreetMap contributors',
        'profile': 'simplified motorcar graph; common to all vehicles',
        'raw_sha256': hashlib.sha256(Path(raw).read_bytes()).hexdigest(),
        'coordinates_source': 'unchanged shared instance coordinates_lonlat',
        'locations_are_synthetic': False,
        'path_objective': 'estimated travel time; distance measured along the SAME selected path',
        'graph_nodes': len(graph), 'depot_strong_component_nodes': len(connected),
        'all_location_pairs_reachable': True, 'snap_method': 'nearest drivable graph vertex',
        'snap_to_depot_component_enabled': snap_to_depot_component,
        'component_resnaps': resnapped,
        'snap_distances_m': snap, 'max_snap_distance_m': max(snap),
        'snapped_coordinates_lonlat': [nodes[u] for u in selected],
        'graph_bbox_wsen': [min(nodes[u][0] for u in graph), min(nodes[u][1] for u in graph),
                            max(nodes[u][0] for u in graph), max(nodes[u][1] for u in graph)],
        'speed_assumptions_kmh': CLASSES,
        'limitations': ['Not OpenRouteService; no turn restriction relations or HGV-specific clearance',
                       'Static road-class speed assumptions capped by parseable maxspeed; no live traffic',
                       'Address-to-road-vertex offsets are audited but not charged as drivable road legs',
                       'Finite extract may exclude better routes; connectivity does not prove boundary independence',
                       'Addresses are from shared source; parking/unloading accessibility is not verified'],
    }
    sidecar = Path(raw).with_suffix('.source.json')
    if sidecar.exists():
        source = json.loads(sidecar.read_text())
        if source.get('sha256') != info['raw_sha256']:
            raise ValueError('OSM source sidecar hash mismatch')
        info['extract_source'] = source
    return distances, durations, info, selected


def attach(instance, distances, durations, metadata, selected=None):
    """Preserve orders, vehicles, costs and original coordinates; update schedules only."""
    coordinates(instance)
    x = copy.deepcopy(instance)
    x['distance_matrix_m'] = distances
    x['duration_matrix_s'] = durations
    x['road_network'] = metadata
    if selected is not None:
        x['osm_node_ids'] = selected
    else:
        x.pop('osm_node_ids', None)
    groups = [[] for _ in x['vehicles']]
    for trip in sorted(x['reference_transports'], key=lambda z: (z['vehicle'], z['start_minutes'])):
        groups[trip['vehicle']].append(trip['customers'])
    x['reference_transports'] = schedule(groups, x)
    # Reported PSO cost belongs to the OLD haversine matrix. Do not silently rescore/relabel it.
    if 'pso_reference_solution' in x:
        x['pso_reference_solution']['comparison_status'] = 'Original non-road-matrix audit only; not a road benchmark competitor'
    x.setdefault('provenance', {})['active_distances'] = 'road_network and duration_matrix_s; original source distances are superseded'
    validate_instance(x)
    # A neutral witness may violate a newly chosen hard minimum; solver validates its
    # capacity/coverage separately and constructs a hard-feasible candidate when needed.
    witness = copy.deepcopy(x)
    witness['model']['stop_count_mode'] = 'soft'
    validate_solution(witness, x['reference_transports'])
    return x


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--instance', type=Path, default=Path('data/shared_pso_250.json'))
    p.add_argument('--output', type=Path, default=Path('data/shared_pso_250_road.json'))
    p.add_argument('--provider', choices=['osm', 'ors'], default='osm')
    p.add_argument('--raw', type=Path, default=Path('cache/budapest_city_osm.json'))
    p.add_argument('--padding', type=float, default=.04)
    p.add_argument('--max-snap-m', type=float, default=200)
    p.add_argument('--snap-to-depot-component', action='store_true',
                   help='Explicitly allow audited snapping to a reachable road vertex within --max-snap-m')
    p.add_argument('--cache', type=Path, default=Path('cache/ors'))
    p.add_argument('--profile', choices=['driving-car', 'driving-hgv'], default='driving-car')
    a = p.parse_args()
    if a.output.resolve() == a.instance.resolve():
        p.error('Output must not overwrite the shared source instance')
    x = json.loads(a.instance.read_text(encoding='utf-8'))
    coords = coordinates(x)
    if a.provider == 'osm':
        if not a.raw.exists():
            download_osm(coords, a.raw, a.padding)
        def progress(done, total):
            if done % 25 == 0 or done == total:
                print(f'Road matrix rows: {done}/{total}', flush=True)
        d, t, info, ids = local_matrices(coords, a.raw, a.max_snap_m, progress, a.snap_to_depot_component)
    else:
        import os
        from road_network import build_matrices, URL
        d, t = build_matrices(coords, os.environ.get('ORS_API_KEY'), a.cache, a.profile)
        info = {'provider': 'openrouteservice', 'map': 'OpenStreetMap contributors',
                'endpoint': URL + a.profile, 'profile': a.profile,
                'coordinates_source': 'unchanged shared instance coordinates_lonlat',
                'locations_are_synthetic': False,
                'limitations': ['Common profile for all vehicles; fleet-specific truck dimensions not enforced',
                                'Static estimated times; no live traffic'],
                'attribution': '© openrouteservice.org by HeiGIT | Map data © OpenStreetMap contributors'}
        ids = None
    info['input_sha256'] = hashlib.sha256(a.instance.read_bytes()).hexdigest()
    y = attach(x, d, t, info, ids)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.output.with_suffix(a.output.suffix + '.tmp')
    tmp.write_text(json.dumps(y, indent=1, allow_nan=False), encoding='utf-8')
    tmp.replace(a.output)
    print(f'Saved {len(coords)}x{len(coords)} directed distance/time matrices: {a.output}')


if __name__ == '__main__':
    main()
