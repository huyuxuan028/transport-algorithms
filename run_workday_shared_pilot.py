"""Run paired GA arms on three frozen Budapest subsets with identical initial plans."""
import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

from build_workday_suite import filtered_schedule
from solver import solve, validate_solution

CASES = (0, 49, 99)
BUDGET = 6032


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(args):
    seed_plan = args.seed_plan.read_bytes()
    starting_trips = json.loads(seed_plan)['best']['transports']
    manifest = json.loads((args.instances / 'manifest.json').read_bytes())
    published = json.loads(args.expected_manifest.read_bytes())
    if manifest != published:
        raise ValueError('Generated suite does not match the published manifest')
    summary, history = [], []
    args.output.mkdir(parents=True)
    for case in args.cases:
        entry = manifest['instances'][case]
        raw = (args.instances / entry['file']).read_bytes()
        if sha(raw) != entry['sha256']:
            raise ValueError('Instance hash does not match local manifest: '+entry['file'])
        instance = json.loads(raw)
        common = filtered_schedule(starting_trips, instance['source_customer_ids'], instance)
        initial = validate_solution(instance, common)
        witness = json.dumps(common, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n'
        (args.output / f'{case:03d}_initial_plan.json').write_bytes(witness.encode())
        for seed in (0, 1, 2):
            for relocate in (False, True):
                arm = 'relocate_only' if relocate else 'original'
                result = solve(instance, seed=seed, population=32, generations=200,
                               objective='cost', evaluation_budget=BUDGET, audit=True,
                               initial_transports=common, relocate=relocate)
                metrics = result['history'][-1]['best_decoded']
                if not result['validation']['feasible'] or not metrics['feasible']:
                    raise ValueError('Expected a feasible final plan from the validated seed')
                if result['combined_evaluations'] != BUDGET:
                    raise ValueError('Expected full budget consumption')
                record = dict(case=case, customers=entry['customers'], seed=seed, arm=arm,
                              instance_sha256=entry['sha256'], initial_plan_sha256=sha(witness.encode()),
                              initial_total_eur=initial['cost']['total_eur'],
                              ga_evaluations=result['evaluations'], local_trials=result['local_trials'],
                              combined_evaluations=result['combined_evaluations'],
                              runtime_seconds=result['runtime_seconds'], **metrics)
                summary.append(record)
                for point in result['history']:
                    history.append(dict(case=case, seed=seed, arm=arm, generation=point['generation'],
                                        combined_evaluations=point['combined_evaluations'], **point['best_decoded']))
                payload = dict(record=record, source_seed_plan_sha256=sha(seed_plan),
                               python=platform.python_version(), result=result)
                (args.output / f'{case:03d}_{arm}_seed_{seed}.json').write_text(
                    json.dumps(payload, indent=2, allow_nan=False)+'\n', encoding='utf-8')
                print(case, seed, arm, round(record['total_eur'], 2), round(record['runtime_seconds'], 2), flush=True)
    for name, rows in [('summary.csv',summary), ('convergence.csv',history)]:
        with (args.output/name).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--instances',type=Path,default=Path('generated/shared_workday_16h'))
    p.add_argument('--expected-manifest',type=Path,default=Path('data/shared_workday_16h_manifest.json'))
    p.add_argument('--seed-plan',type=Path,default=Path('results/workday_16h_seed_comparison/seeded.json'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',type=int,nargs='+',choices=CASES,default=CASES)
    run(p.parse_args())
