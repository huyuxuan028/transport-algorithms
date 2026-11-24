"""Materialize the shared GA/PSO Budapest 16-hour benchmark suite."""

import argparse
import hashlib
import json
from pathlib import Path

from solver import schedule, validate_instance, validate_solution


SOURCE_SHA256 = '6d794dff4a03cebb1f9127796209fa1f263450a780ce76ade9c26244b6a2676c'
VERSION = 'budapest-workday-16h-v1'
HORIZON_MINUTES = 960


def digest(data):
    return hashlib.sha256(data).hexdigest()


def legacy_sum(values):
    """Preserve the original v1 Python 3.11 floating-point accumulation."""
    total = 0
    for value in values:
        total += value
    return total


def filtered_schedule(transports, source_ids, instance, *, stable_v1=False):
    new_ids = {source_id: new_id for new_id, source_id in enumerate(source_ids)}
    groups = [[] for _ in instance['vehicles']]
    for trip in transports:
        route = [new_ids[node] for node in trip['customers'] if node in new_ids]
        if route:
            groups[trip['vehicle']].append(route)
    if stable_v1:
        return schedule(groups, instance, summation=legacy_sum)
    return schedule(groups, instance)


def build_case(source, seed):
    count = 150 + seed
    ranked = sorted(range(1, 251), key=lambda node: digest(f'{VERSION}:{seed}:{node}'.encode('ascii')))
    source_ids = [0] + sorted(ranked[:count])
    name = f'{VERSION}-{seed:03d}'
    subset = {
        key: source[key] for key in (
            'schema_version', 'cycles_per_vehicle', 'fleet_size', 'vehicle_types', 'vehicles', 'provenance')
    }
    subset.update(name=name, seed=seed, source_customer_ids=source_ids)
    subset['model'] = dict(source['model'], time_horizon_minutes=HORIZON_MINUTES, stop_count_mode='soft')
    subset['customers'] = [dict(source['customers'][i], id=j) for j, i in enumerate(source_ids)]
    for key in ('coordinates_km', 'coordinates_lonlat', 'osm_node_ids'):
        subset[key] = [source[key][i] for i in source_ids]
    for key in ('distance_matrix_m', 'duration_matrix_s'):
        matrix = source[key]
        subset[key] = [[matrix[i][j] for j in source_ids] for i in source_ids]

    road = source['road_network']
    metadata = dict(road, parent_road_sha256=SOURCE_SHA256)
    for key in ('snap_distances_m', 'snapped_coordinates_lonlat'):
        metadata[key] = [road[key][i] for i in source_ids]
    metadata['max_snap_distance_m'] = max(metadata['snap_distances_m'])
    new_ids = {source_id: new_id for new_id, source_id in enumerate(source_ids)}
    metadata['component_resnaps'] = [
        dict(entry, customer_id=new_ids[entry['customer_id']])
        for entry in road['component_resnaps'] if entry['customer_id'] in new_ids
    ]
    subset['road_network'] = metadata
    subset['reference_transports'] = filtered_schedule(source['reference_transports'], source_ids, subset, stable_v1=True)
    return subset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('data/shared_pso_250_road.json'))
    parser.add_argument('--output', type=Path, default=Path('generated/shared_workday_16h'))
    args = parser.parse_args()
    raw = args.source.read_bytes()
    if digest(raw) != SOURCE_SHA256:
        parser.error(f'Expected the frozen shared road input with SHA-256 {SOURCE_SHA256}')
    source = json.loads(raw)
    args.output.mkdir(parents=True)
    entries = []
    for seed in range(100):
        instance = build_case(source, seed)
        validate_instance(instance)
        witness_model = dict(instance['model'], time_horizon_minutes=None)
        validate_solution(dict(instance, model=witness_model), instance['reference_transports'])
        filename = instance['name'] + '.json'
        data = (json.dumps(instance, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
        (args.output / filename).write_bytes(data)
        entries.append({'file': filename, 'seed': seed, 'customers': len(instance['customers']) - 1, 'sha256': digest(data)})
    manifest = {
        'suite': VERSION,
        'source_sha256': SOURCE_SHA256,
        'workday_start_local': '08:00',
        'time_horizon_minutes': HORIZON_MINUTES,
        'instances': entries,
    }
    (args.output / 'manifest.json').write_bytes((json.dumps(manifest, indent=2) + '\n').encode('utf-8'))
    print(f"Wrote {len(entries)} instances and manifest to {args.output}")


if __name__ == '__main__':
    main()
