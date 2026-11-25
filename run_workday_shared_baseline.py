"""Run the original GA on the frozen 100-case Budapest suite with checkpoints."""

import argparse
import csv
import io
import json
import os
import platform
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from build_workday_suite import HORIZON_MINUTES, filtered_schedule
from run_workday_shared_pilot import BUDGET, sha
from solver import solve, validate_solution


FIELDS = (
    'case', 'customers', 'status', 'feasible', 'initial_max_vehicle_minutes',
    'real_cost_eur', 'penalty_eur', 'total_eur', 'short_trips', 'max_vehicle_minutes',
    'evaluations', 'runtime_seconds', 'local_trials', 'instance_sha256', 'initial_plan_sha256', 'error',
)


def atomic_write(path, raw):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False) + '\n').encode('utf-8')


def load_instance(path, entry):
    raw = path.read_bytes()
    if sha(raw) != entry['sha256']:
        raise ValueError(f'Instance SHA-256 mismatch: {path}')
    instance = json.loads(raw)
    if instance['model']['time_horizon_minutes'] != HORIZON_MINUTES:
        raise ValueError(f'Instance does not use the 960-minute horizon: {path}')
    return instance


def run_case(path, entry, row, initial_plan):
    started = time.perf_counter()
    result = None
    try:
        instance = load_instance(path, entry)
        result = solve(instance, seed=0, population=32, generations=200, objective='cost',
                       evaluation_budget=BUDGET, initial_transports=initial_plan,
                       relocate=False, swap=False, audit=True)
        row.update(evaluations=result['evaluations'], runtime_seconds=result['runtime_seconds'],
                   local_trials=result['local_trials'])
        if not result['validation']['feasible']:
            raise ValueError('GA returned no feasible final schedule')
        if result['evaluations'] > BUDGET or result['local_trials'] != 0:
            raise ValueError('Unexpected evaluation counts for original GA')
        metrics = result['history'][-1]['best_decoded']
        row.update(status='completed', feasible=True)
        for field in ('real_cost_eur', 'penalty_eur', 'total_eur', 'short_trips', 'max_vehicle_minutes'):
            row[field] = metrics[field]
    except Exception as error:
        row.update(status='failed', feasible=False, error=f'{type(error).__name__}: {error}')
        row.setdefault('runtime_seconds', time.perf_counter()-started)
    return dict(record=row, result=result)


def write_summaries(output, completed, planned):
    rows = [completed[i] for i in sorted(completed)]
    feasible = [row for row in rows if row['feasible']]
    failures = [row for row in rows if not row['feasible']]
    for name, selected in [('summary.csv', rows), ('failures.csv', failures)]:
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(selected)
        atomic_write(output/name, stream.getvalue().encode('utf-8'))
    zero_penalty = sum(row['penalty_eur']==0 for row in feasible)
    totals = dict(planned=planned, recorded=len(rows), pending=planned-len(rows), feasible=len(feasible),
                  failed=len(failures), zero_penalty=zero_penalty, feasible_rate=len(feasible)/planned,
                  zero_penalty_rate_all=zero_penalty/planned,
                  zero_penalty_rate_feasible=zero_penalty/len(feasible) if feasible else None)
    atomic_write(output/'totals.json', json_bytes(totals))
    return totals


def run(args):
    manifest_raw = args.expected_manifest.read_bytes()
    manifest = json.loads(manifest_raw)
    if json.loads((args.instances/'manifest.json').read_bytes()) != manifest:
        raise ValueError('Generated suite manifest does not match the repository manifest')
    entries = manifest['instances']
    if [entry['seed'] for entry in entries] != list(range(100)):
        raise ValueError('Expected all 100 cases numbered 0 through 99')
    seed_raw = args.seed_plan.read_bytes()
    starting_trips = json.loads(seed_raw)['best']['transports']
    config = dict(manifest_sha256=sha(manifest_raw), seed_plan_sha256=sha(seed_raw),
                  solver_sha256=sha(Path(__file__).with_name('solver.py').read_bytes()),
                  python=platform.python_version(), seed=0, population=32, generations=200,
                  evaluation_budget=BUDGET, relocate=False, swap=False)
    output = args.output
    case_dir = output/'cases'
    if args.resume:
        if json.loads((output/'run_config.json').read_bytes()) != config:
            raise ValueError('Checkpoint configuration differs from the requested run')
    else:
        output.mkdir(parents=True)
        case_dir.mkdir()
        atomic_write(output/'run_config.json', json_bytes(config))

    completed, jobs = {}, []
    for entry in entries:
        case = entry['seed']
        path = args.instances/entry['file']
        instance = load_instance(path, entry)
        plan = filtered_schedule(starting_trips, instance['source_customer_ids'], instance)
        witness = (json.dumps(plan, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()
        row = dict(case=case, customers=entry['customers'], instance_sha256=entry['sha256'],
                   initial_plan_sha256=sha(witness))
        checkpoint = case_dir/f'{case:03d}.json'
        try:
            checked = validate_solution(instance, plan)
        except ValueError as error:
            row.update(status='invalid_initial_plan', feasible=False, evaluations=0, local_trials=0,
                       error=f'{type(error).__name__}: {error}')
            atomic_write(checkpoint, json_bytes(dict(record=row, result=None)))
            completed[case] = row
            continue
        row['initial_max_vehicle_minutes'] = max(checked['finish_minutes_by_vehicle'])
        if checkpoint.exists():
            saved = json.loads(checkpoint.read_bytes())['record']
            if any(saved.get(field)!=value for field,value in row.items()):
                raise ValueError(f'Checkpoint does not match verified inputs: {checkpoint}')
            completed[case] = saved
        else:
            jobs.append((path, entry, row, plan))
    if len(completed)+len(jobs)!=100:
        raise RuntimeError('Incomplete suite preflight')
    invalid = sum(row['status']=='invalid_initial_plan' for row in completed.values())
    print(f'100 SHA-256 hashes verified; {100-invalid}/100 initial plans feasible; '
          f'{len(completed)} recorded; {len(jobs)} pending', flush=True)
    totals = write_summaries(output, completed, len(entries))
    if jobs:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(run_case, *job) for job in jobs]
            for future in as_completed(futures):
                payload = future.result()
                row = payload['record']
                case = row['case']
                atomic_write(case_dir/f'{case:03d}.json', json_bytes(payload))
                completed[case] = row
                totals = write_summaries(output, completed, len(entries))
                print(f"{len(completed)}/100 case={case:03d} {row['status']} "
                      f"total={row.get('total_eur')} seconds={row.get('runtime_seconds', 0):.2f}", flush=True)
    print(json.dumps(totals), flush=True)
    return 1 if totals['failed'] else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instances', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-manifest', type=Path, default=Path('data/shared_workday_16h_manifest.json'))
    parser.add_argument('--seed-plan', type=Path, default=Path('results/workday_16h_seed_comparison/seeded.json'))
    parser.add_argument('--jobs', type=int, default=4, help='Parallel instance workers')
    parser.add_argument('--resume', action='store_true', help='Keep recorded successes and failures; run pending cases')
    arguments = parser.parse_args()
    if arguments.jobs < 1:
        parser.error('--jobs must be positive')
    raise SystemExit(run(arguments))
