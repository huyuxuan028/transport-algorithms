"""Compare the original and cross-trip GA on the frozen Budapest workday case."""

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

from build_workday_suite import HORIZON_MINUTES, SOURCE_SHA256
from solver import solve

BUDGET = 6032
LOCAL_LIMIT = 40
SEED_PLAN = Path('results/workday_16h_seed_comparison/seeded.json')
ARMS = {'original': '#276e9c', 'relocate_swap': '#b44927'}
ISOLATED_ARMS = {'original': '#276e9c', 'swap_only': '#b44927', 'relocate_only': '#26804b'}
LABELS = {'original': 'Original GA', 'relocate_swap': 'Relocate + swap',
          'swap_only': 'Swap only', 'relocate_only': 'Relocate only'}
DASHES = {'original': '', 'relocate_swap': '5 3', 'swap_only': '5 3', 'relocate_only': '2 4'}


def write_csv(path, rows):
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_chart(path, rows, arms):
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="880" height="740" viewBox="0 0 880 740">',
             '<rect width="880" height="740" fill="white"/>',
             '<g font-family="sans-serif" fill="#20252b" font-size="13">',
             '<text x="28" y="28" font-size="20">Budapest 250 — best feasible cost (EUR)</text>',
             ]
    for index, (arm,color) in enumerate(arms.items()):
        x = 28 + 150*index
        lines.append(f'<path d="M{x} 48h18" stroke="{color}" stroke-width="2" stroke-dasharray="{DASHES[arm] or "none"}"/>')
        lines.append(f'<text x="{x+24}" y="52" fill="{color}">{LABELS[arm]}</text>')
    left, width, height = 115, 725, 155
    for seed in range(3):
        points = [row for row in rows if row['seed'] == seed]
        top = 83 + 197 * seed
        scores = [row['total_eur'] for row in points]
        low, high = min(scores), max(scores)
        margin = max(1, (high - low) * 0.1)
        low, high = low - margin, high + margin
        lines.append(f'<text x="{left}" y="{top-7}">Seed {seed}</text>')
        for tick in range(5):
            y = top + height * tick / 4
            value = high - (high - low) * tick / 4
            lines.append(f'<path d="M{left} {y}h{width}" stroke="#ddd"/>')
            lines.append(f'<text x="{left-8}" y="{y+4}" text-anchor="end">{value:,.0f}</text>')
        for arm, color in arms.items():
            coords = []
            for row in points:
                if row['arm'] != arm:
                    continue
                x = left + width * row['combined_evaluations'] / BUDGET
                y = top + height * (high - row['total_eur']) / (high - low)
                coords.append(f'{x:.2f},{y:.2f}')
            dash = f' stroke-dasharray="{DASHES[arm]}"' if DASHES[arm] else ''
            lines.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{color}" stroke-width="2"{dash}/>')
    for tick in range(5):
        x = left + width * tick / 4
        lines.append(f'<text x="{x}" y="655" text-anchor="middle">{BUDGET*tick/4:,.0f}</text>')
    lines.append('<text x="477" y="682" text-anchor="middle">GA candidates + cross-trip trials</text></g></svg>')
    with path.open('x', encoding='utf-8') as stream:
        stream.write('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--isolated-operators', action='store_true',
                        help='Compare original, swap-only, and relocate-only arms')
    args = parser.parse_args()
    raw = Path('data/shared_pso_250_road.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        parser.error('The frozen Budapest road input has the wrong SHA-256')
    instance = json.loads(raw)
    instance['model']['time_horizon_minutes'] = HORIZON_MINUTES
    seed_raw = SEED_PLAN.read_bytes()
    seed_transports = json.loads(seed_raw)['best']['transports']
    args.output.mkdir(parents=True)
    arms = ISOLATED_ARMS if args.isolated_operators else ARMS
    summary, convergence, rejection_rows = [], [], []
    for seed in range(3):
        for arm in arms:
            relocate = arm in ('relocate_swap','relocate_only')
            swap = arm in ('relocate_swap','swap_only')
            result = solve(instance, seed=seed, population=32, generations=200,
                           objective='cost', evaluation_budget=BUDGET, audit=True,
                           initial_transports=seed_transports, relocate=relocate, swap=swap,
                           cross_trip_trials_per_generation=LOCAL_LIMIT)
            result.update(arm=arm, source_sha256=SOURCE_SHA256, evaluation_budget=BUDGET,
                          seed_plan=str(SEED_PLAN.as_posix()), seed_plan_sha256=hashlib.sha256(seed_raw).hexdigest(),
                          time_horizon_minutes=HORIZON_MINUTES, local_limit_per_generation=LOCAL_LIMIT if relocate or swap else 0,
                          python=platform.python_version(), platform=platform.platform())
            with (args.output / f'{arm}_seed_{seed}.json').open('x', encoding='utf-8') as stream:
                json.dump(result, stream, indent=2, allow_nan=False)
            for point in result['history']:
                convergence.append(dict(seed=seed, arm=arm, generation=point['generation'],
                                        ga_evaluations=point['evaluations'], local_trials=point['local_trials'],
                                        combined_evaluations=point['combined_evaluations'], **point['best_decoded']))
            summary.append({**convergence[-1], 'runtime_seconds': result['runtime_seconds']})
            if relocate:
                rejection_rows.append(dict(seed=seed, arm=arm, **result['cross_trip_counts']['relocate'],
                                           **result['relocate_rejections'],
                                           **{f'screened_pairs_{key}': count for key, count in result['relocate_screened_route_pairs'].items()}))
            print(summary[-1], result['cross_trip_counts'], result['relocate_rejections'], flush=True)
    write_csv(args.output / 'summary.csv', summary)
    write_csv(args.output / 'convergence.csv', convergence)
    if rejection_rows:
        write_csv(args.output / 'relocate_rejections.csv', rejection_rows)
    write_chart(args.output / 'convergence.svg', convergence, arms)


if __name__ == '__main__':
    main()
