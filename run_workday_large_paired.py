"""Reproduce the paired GA comparison for shared cases 074, 075, and 099."""

import argparse
import csv
import json
import platform
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from build_workday_suite import filtered_schedule
from run_workday_shared_pilot import BUDGET, sha
from solver import solve, validate_solution

CASES = (74, 75, 99)
BASELINE = Path('results/workday_16h_shared_baseline_seed0')
PILOT = Path('results/workday_16h_shared_pilot_local')
SEED_PLAN = Path('results/workday_16h_seed_comparison/seeded.json')


def run_case(path, plan, seed, relocate):
    return solve(json.loads(path.read_bytes()), seed=seed, population=32, generations=200,
                 objective='cost', evaluation_budget=BUDGET, audit=True,
                 initial_transports=plan, relocate=relocate, swap=False)


def validate_record(instance, plan, result, seed, relocate):
    expected = dict(seed=seed, method='ga', objective='cost', population=32, generations=200,
                    heuristic_seed=True, local_search=True, crossover_rate=0.9, stop_count_mode='soft')
    if any(result.get(k) != v for k, v in expected.items()):
        raise ValueError('Run settings do not match')
    if result['baseline_decoded']['transports'] != plan:
        raise ValueError('Supplied initial schedule differs')
    if set(result['cross_trip_counts']) != ({'relocate'} if relocate else set()):
        raise ValueError('Operator settings do not match')
    if result['evaluations']+result['local_trials'] != result['combined_evaluations'] or result['combined_evaluations'] > BUDGET:
        raise ValueError('Run exceeded its budget or evaluation counts disagree')
    if not relocate and result['local_trials']:
        raise ValueError('Original GA recorded local trials')
    final = validate_solution(instance, result['best']['transports'], result['best']['fleet'])
    if final != result['validation']:
        raise ValueError('Final schedule metrics do not match revalidation')
    return final


def write_json(path, payload):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instances', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    manifest_raw = Path('data/shared_workday_16h_manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    if json.loads((args.instances/'manifest.json').read_bytes()) != manifest:
        raise ValueError('Instance manifest differs from the repository manifest')
    seed_raw = SEED_PLAN.read_bytes()
    starting_trips = json.loads(seed_raw)['best']['transports']
    config = dict(manifest_sha256=sha(manifest_raw), seed_plan_sha256=sha(seed_raw),
                  solver_sha256=sha(Path('solver.py').read_bytes()),
                  cross_trip_search_sha256=sha(Path('cross_trip_search.py').read_bytes()),
                  python=platform.python_version(), population=32, generations=200,
                  evaluation_budget=BUDGET, swap=False)
    baseline_metadata = BASELINE/'run_config.json'
    baseline_config = json.loads(baseline_metadata.read_bytes()) if baseline_metadata.exists() else {}
    reusable_baseline = all(baseline_config.get(k)==v for k,v in config.items() if k!='cross_trip_search_sha256')
    reusable_baseline &= baseline_config.get('seed')==0 and baseline_config.get('relocate') is False
    args.output.mkdir(parents=True)
    write_json(args.output/'run_config.json', config)
    prepared, pending, records, decisions = {}, [], [], []

    def save(case, seed, arm, result, source):
        instance, plan, record = prepared[case]
        final = validate_record(instance, plan, result, seed, arm=='relocate_only')
        row = dict(case=f'{case:03d}', seed=seed, arm=arm, **record, feasible=True,
                   real_cost_eur=final['cost']['real_cost_eur'], penalty_eur=final['cost']['penalty_eur'],
                   total_eur=final['cost']['total_eur'], max_vehicle_minutes=max(final['finish_minutes_by_vehicle']),
                   ga_evaluations=result['evaluations'], local_trials=result['local_trials'],
                   combined_evaluations=result['combined_evaluations'], runtime_seconds=result['runtime_seconds'],
                   provenance='reused' if source else 'rerun', reused_from=source.as_posix() if source else '')
        write_json(args.output/f'{case:03d}_{arm}_seed_{seed}.json', dict(record=row, result=result))
        records.append(row)
        print(case, seed, arm, row['provenance'], row['penalty_eur'], row['total_eur'], flush=True)

    for case in CASES:
        entry = manifest['instances'][case]
        path = args.instances/entry['file']
        raw = path.read_bytes()
        if sha(raw) != entry['sha256']:
            raise ValueError(f'Instance hash mismatch: {path}')
        instance = json.loads(raw)
        plan = filtered_schedule(starting_trips, instance['source_customer_ids'], instance)
        initial = validate_solution(instance, plan)
        witness = (json.dumps(plan, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()
        (args.output/f'{case:03d}_initial_plan.json').write_bytes(witness)
        identity = dict(instance_sha256=entry['sha256'], initial_plan_sha256=sha(witness))
        prepared[case] = (instance, plan, dict(customers=entry['customers'], **identity,
                                              initial_total_eur=initial['cost']['total_eur']))
        for seed in (0,1,2):
            for arm in ('original','relocate_only'):
                source = BASELINE/'cases'/f'{case:03d}.json' if seed==0 and arm=='original' else PILOT/f'{case:03d}_{arm}_seed_{seed}.json'
                if source.exists() and source.is_relative_to(BASELINE) and reusable_baseline:
                    prior = json.loads(source.read_bytes())
                    try:
                        if any(prior['record'].get(key)!=value for key,value in identity.items()):
                            raise ValueError('Instance or initial schedule hash differs')
                        save(case,seed,arm,prior['result'],source)
                    except (KeyError,ValueError) as error:
                        decisions.append(dict(case=case, seed=seed, arm=arm, reason=str(error)))
                    else:
                        decisions.append(dict(case=case, seed=seed, arm=arm, reason='Reused matching baseline checkpoint'))
                        continue
                else:
                    reason = ('Existing pilot checkpoint has no solver fingerprint' if source.exists() and source.is_relative_to(PILOT)
                              else 'No checkpoint with matching solver and settings')
                    decisions.append(dict(case=case, seed=seed, arm=arm, reason=reason))
                pending.append((case,seed,arm,path,plan))
    write_json(args.output/'reuse_decisions.json', decisions)
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_case,path,plan,seed,arm=='relocate_only'):(case,seed,arm)
                   for case,seed,arm,path,plan in pending}
        for future in as_completed(futures):
            case, seed, arm = futures[future]
            save(case,seed,arm,future.result(),None)
    records.sort(key=lambda row:(row['case'],row['seed'],row['arm']))
    with (args.output/'summary.csv').open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


if __name__ == '__main__':
    main()
