"""Paired original/relocate-only GA for shared Budapest cases 075 through 099."""

import argparse
import csv
import io
import json
import platform
import statistics
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from decimal import Decimal
from pathlib import Path

from build_workday_suite import filtered_schedule
from run_workday_large_paired import BASELINE, SEED_PLAN, run_case, validate_record
from run_workday_shared_baseline import atomic_write, json_bytes, load_instance
from run_workday_shared_pilot import BUDGET, sha
from solver import validate_solution

CASES = range(75, 100)
ARMS = ('original', 'relocate_only')
PREVIOUS = Path('results/workday_16h_large_paired')
METRICS = ('real_cost_eur', 'penalty_eur', 'total_eur', 'runtime_seconds')


def save_csv(path, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    atomic_write(path, stream.getvalue().encode('utf-8'))


def summarize(output, records):
    save_csv(output/'summary.csv', [records[case, arm] for case in CASES for arm in ARMS])
    pairs = []
    for case in CASES:
        original, relocate = (records[case, arm] for arm in ARMS)
        delta = {metric: Decimal(str(original[metric]))-Decimal(str(relocate[metric])) for metric in METRICS}
        outcome = 'win' if delta['total_eur'] > 0 else 'loss' if delta['total_eur'] < 0 else 'tie'
        pairs.append(dict(case=original['case'], customers=original['customers'], outcome=outcome,
                          **{f'original_minus_relocate_{key}': value for key,value in delta.items()}))
    save_csv(output/'paired_deltas.csv', pairs)
    counts = Counter(pair['outcome'] for pair in pairs)
    median_penalty = statistics.median(pair['original_minus_relocate_penalty_eur'] for pair in pairs)
    stats = {}
    for arm in ARMS:
        rows = [records[case, arm] for case in CASES]
        stats[arm] = dict(zero_penalty=sum(row['penalty_eur']==0 for row in rows),
                          reused=sum(row['provenance']=='reused' for row in rows),
                          **{f'mean_{k}':statistics.mean(row[k] for row in rows) for k in METRICS})
    totals = dict(pairs=len(pairs), wins=counts['win'], ties=counts['tie'], losses=counts['loss'],
                  median_penalty_reduction_eur=float(median_penalty), **stats)
    atomic_write(output/'totals.json', json_bytes(totals))
    table = '\n'.join(
        f"| {label} | {stats[arm]['mean_real_cost_eur']:,.2f} | {stats[arm]['mean_penalty_eur']:,.2f} | "
        f"{stats[arm]['mean_total_eur']:,.2f} | {stats[arm]['mean_runtime_seconds']:.2f} | "
        f"{stats[arm]['zero_penalty']}/25 ({stats[arm]['zero_penalty']*4}%) |"
        for arm,label in zip(ARMS,('Original GA','Relocate only')))
    report = f"""# Budapest shared cases 075-099: seed-0 GA comparison

All 50 final schedules passed revalidation. On the penalty-inclusive
objective, relocate-only recorded **{counts['win']} wins, {counts['tie']} ties,
and {counts['loss']} losses** across 25 pairs. The median paired penalty
reduction (original minus relocate) was **EUR {median_penalty:,.2f}**.

| Arm | Mean operating cost (EUR) | Mean soft penalty (EUR) | Mean total objective (EUR) | Mean recorded runtime (s) | Zero penalty |
|---|---:|---:|---:|---:|---:|
{table}

Cases have 225-249 addresses. Each pair shared the same verified initial
schedule, seed 0, population 32, a limit of 200 generations, and a cap of
6,032 counted operations. Swap was disabled. One GA candidate evaluation
and one cross-trip trial each debit one unit, with different computational
costs. The per-run CSV gives GA evaluations and local trials separately.

Reused {stats['original']['reused']} original and {stats['relocate_only']['reused']}
relocate-only checkpoints after checking instance and initial-plan hashes,
solver fingerprints, and settings. Runtimes retain the original measurement
conditions for reused checkpoints. The means are descriptive because the
runs were recorded in different batches with parallel workers.

To reproduce from the repository root, use a fresh output directory:

```powershell
python run_workday_large_seed0.py --instances generated/shared_workday_16h_pilot_local --output results/workday_16h_large_seed0_repro --jobs 8
```

To resume, use the same command and output directory with `--resume`.

[Per-run summary](summary.csv) · [Paired differences](paired_deltas.csv) ·
[Aggregate statistics](totals.json)
"""
    atomic_write(output/'REPORT.md', report.encode('utf-8'))
    print(json.dumps(totals), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instances', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    manifest_raw = Path('data/shared_workday_16h_manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    if json.loads((args.instances/'manifest.json').read_bytes()) != manifest:
        raise ValueError('Suite manifest differs from the repository manifest')
    seed_raw = SEED_PLAN.read_bytes()
    starting_trips = json.loads(seed_raw)['best']['transports']
    fingerprints = dict(manifest_sha256=sha(manifest_raw), seed_plan_sha256=sha(seed_raw),
                        solver_sha256=sha(Path('solver.py').read_bytes()),
                        cross_trip_search_sha256=sha(Path('cross_trip_search.py').read_bytes()),
                        python=platform.python_version(), population=32, generations=200,
                        evaluation_budget=BUDGET, swap=False)
    config = dict(**fingerprints, seed=0, cases=list(CASES))
    output = args.output
    config_path = output/'run_config.json'
    if args.resume:
        if json.loads(config_path.read_bytes()) != config:
            raise ValueError('Current configuration differs from the checkpoints')
    else:
        output.mkdir(parents=True)
        atomic_write(config_path, json_bytes(config))

    def matches(source, expected):
        metadata = source/'run_config.json'
        if not metadata.exists():
            return False
        actual = json.loads(metadata.read_bytes())
        return all(actual.get(k)==v for k,v in expected.items())

    original_settings = {k:v for k,v in fingerprints.items() if k!='cross_trip_search_sha256'}
    reusable = {'original':matches(BASELINE,dict(original_settings, seed=0, relocate=False)),
                'relocate_only':matches(PREVIOUS,fingerprints)}
    cases = {}
    for case in CASES:
        entry = manifest['instances'][case]
        path = args.instances/entry['file']
        instance = load_instance(path,entry)
        plan = filtered_schedule(starting_trips,instance['source_customer_ids'],instance)
        initial = validate_solution(instance,plan)
        witness = (json.dumps(plan,sort_keys=True,separators=(',', ':'),allow_nan=False)+'\n').encode()
        identity = dict(instance_sha256=entry['sha256'],initial_plan_sha256=sha(witness))
        cases[case] = (path,instance,plan,identity,initial['cost']['total_eur'])

    records, pending = {}, []
    def checkpoint(case,arm):
        return output/f'{case:03d}_{arm}_seed_0.json'

    def save(case,arm,result,source=None,resume=False):
        _,instance,plan,identity,initial_total = cases[case]
        final = validate_record(instance,plan,result,0,arm=='relocate_only')
        row = dict(case=f'{case:03d}',customers=len(instance['customers'])-1,seed=0,arm=arm,
                   **identity,initial_total_eur=initial_total,feasible=True,
                   **{k:final['cost'][k] for k in METRICS[:3]},
                   runtime_seconds=result['runtime_seconds'],
                   max_vehicle_minutes=max(final['finish_minutes_by_vehicle']),
                   ga_evaluations=result['evaluations'],local_trials=result['local_trials'],
                   combined_evaluations=result['combined_evaluations'],
                   provenance='reused' if source else 'rerun',reused_from=source or '')
        if not resume:
            atomic_write(checkpoint(case,arm),json_bytes(dict(record=row,result=result)))
        records[case,arm] = row

    for case in CASES:
        identity = cases[case][3]
        for arm in ARMS:
            target = checkpoint(case,arm)
            source = BASELINE/'cases'/f'{case:03d}.json' if arm=='original' else PREVIOUS/target.name
            existing = target if target.exists() else source if reusable[arm] and source.exists() else None
            if existing is not None:
                try:
                    payload = json.loads(existing.read_bytes())
                    rec = payload['record']
                    if any(rec.get(k)!=v for k,v in identity.items()):
                        raise ValueError('Stored hashes differ')
                    reused_from = (rec.get('reused_from') or None) if existing==target else source.as_posix()
                    save(case,arm,payload['result'],reused_from,resume=existing==target)
                except (ValueError,KeyError,TypeError) as error:
                    print(f'{case:03d} {arm} checkpoint mismatch: {error}',flush=True)
                else:
                    continue
            pending.append((case,arm))
    print(f'25 instance hashes and initial schedules verified; {len(records)}/50 recorded; {len(pending)} pending',flush=True)
    failures = []
    if pending:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(run_case,cases[case][0],cases[case][2],0,arm=='relocate_only'):(case,arm)
                       for case,arm in pending}
            for future in as_completed(futures):
                case,arm = futures[future]
                try:
                    save(case,arm,future.result())
                except Exception as error:
                    failures.append(dict(case=case,arm=arm,error=f'{type(error).__name__}: {error}'))
                    atomic_write(output/'failures.json',json_bytes(failures))
                    print(f'{case:03d} {arm} failed: {error}',flush=True)
                else:
                    print(f'{len(records)}/50 {case:03d} {arm} validated',flush=True)
    atomic_write(output/'failures.json',json_bytes(failures))
    if failures:
        return 1
    summarize(output,records)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
