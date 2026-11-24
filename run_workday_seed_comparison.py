"""Run one matched-budget seeded/unseeded GA comparison on Budapest 250."""

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

from build_workday_suite import HORIZON_MINUTES, SOURCE_SHA256
from solver import solve


def write_convergence_chart(output_dir):
    with (output_dir / 'convergence.csv').open(encoding='utf-8', newline='') as source:
        rows = list(csv.DictReader(source))
    arms = {'seeded': '#146f8a', 'unseeded': '#b84c2c'}
    panels = [
        ('Feasible population (%)', 'feasible_rate', 100),
        ('Best feasible objective (EUR)', 'feasible_best_total_eur', 1),
        ('Best decoded horizon excess (minutes)', 'best_decoded_horizon_excess_minutes', 1),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="680" viewBox="0 0 880 680">',
        '<rect width="880" height="680" fill="white"/>',
        '<g font-family="sans-serif" fill="#20252b" font-size="13">',
        '<text x="32" y="31" font-size="20">Budapest 250: GA initialization comparison</text>',
        '<text x="32" y="55" fill="#146f8a">Seeded</text>',
        '<text x="105" y="55" fill="#b84c2c">Unseeded</text>',
    ]
    left, width, height = 95, 745, 140
    budget = max(int(row['evaluations']) for row in rows)
    for index, (title, field, multiplier) in enumerate(panels):
        top = 92 + 187 * index
        values = [float(row[field]) * multiplier for row in rows if row[field]]
        low, high = (0, 100) if index == 0 else (min(values, default=0), max(values, default=1))
        if index == 2:
            low = 0
        if low == high:
            high, low = high + max(1, high * 0.01), max(0, low - max(1, low * 0.01))
        parts.append(f'<text x="{left}" y="{top-10}">{title}</text>')
        for tick in range(5):
            y = top + height * tick / 4
            value = high - (high - low) * tick / 4
            parts.append(f'<path d="M{left} {y}h{width}" stroke="#ddd"/>')
            parts.append(f'<text x="{left-8}" y="{y+4}" text-anchor="end">{value:,.0f}</text>')
        for arm, color in arms.items():
            points = []
            for row in rows:
                if row['arm'] != arm or not row[field]:
                    continue
                x = left + width * int(row['evaluations']) / budget
                y = top + height * (high - float(row[field]) * multiplier) / (high - low)
                points.append(f'{x:.2f},{y:.2f}')
            if points:
                dash = ' stroke-dasharray="6 4"' if arm == 'unseeded' else ''
                parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"{dash}/>')
    for tick in range(5):
        x = left + width * tick / 4
        parts.append(f'<text x="{x}" y="627" text-anchor="middle">{budget*tick/4:,.0f}</text>')
    parts.append('<text x="468" y="653" text-anchor="middle">Candidate evaluations</text></g></svg>')
    with (output_dir / 'convergence.svg').open('x', encoding='utf-8') as chart:
        chart.write('\n'.join(parts) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--plot-only', action='store_true', help='Render an existing convergence CSV')
    args = parser.parse_args()
    if args.plot_only:
        write_convergence_chart(args.output)
        return
    raw = Path('data/shared_pso_250_road.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        parser.error('The frozen shared road file does not match its SHA-256')
    instance = json.loads(raw)
    instance['model']['time_horizon_minutes'] = HORIZON_MINUTES
    args.output.mkdir(parents=True)
    rows = []
    for label, seeded in [('seeded', True), ('unseeded', False)]:
        result = solve(instance, seed=0, population=32, generations=200, objective='cost',
                       heuristic_seed=seeded, evaluation_budget=6032, audit=True)
        result.update(source_sha256=SOURCE_SHA256, python=platform.python_version(),
                      platform=platform.platform(), evaluation_budget=6032,
                      time_horizon_minutes=HORIZON_MINUTES)
        with (args.output / f'{label}.json').open('x', encoding='utf-8') as output:
            json.dump(result, output, indent=2, allow_nan=False)
        for point in result['history']:
            rows.append({
                'arm': label,
                **{key: point[key] for key in ('generation', 'evaluations', 'feasible_population', 'population_size')},
                'feasible_rate': point['feasible_population'] / point['population_size'],
                'feasible_best_total_eur': point['objective'],
                **{f'best_decoded_{key}': value for key, value in (point['best_decoded'] or {}).items()},
            })
        print(label, result['evaluations'], result['runtime_seconds'], result['validation']['feasible'], flush=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (args.output / 'convergence.csv').open('x', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    write_convergence_chart(args.output)


if __name__ == '__main__':
    main()
