"""Bidirectional cross-evaluator for GA and PSO solutions.

Evaluates:
  1. PSO plans using GA's evaluator (solver.validate_solution).
  2. GA plans using PSO's evaluator (src.cost.trip_metrics, day_metrics, decoder.check_solution).

All instance, solution, and dataset paths are passed dynamically via function
arguments or CLI flags. No environment-specific paths are hardcoded.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import solver


def _ensure_pso_imported(pso_repo_path: str | Path | None = None):
    """Dynamically import PSO packages from the specified or discovered directory."""
    if 'src.data_loader' in sys.modules:
        return
    candidates = []
    if pso_repo_path:
        candidates.append(Path(pso_repo_path).resolve())
    candidates.append(ROOT.parent / 'industrial-transport')
    for c in candidates:
        if (c / 'src/data_loader.py').exists():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            return
    raise ImportError(
        f"Could not locate industrial-transport repository. Please provide --pso-repo. Searched: {candidates}"
    )


def evaluate_pso_with_ga(
    pso_solution_path: str | Path,
    ga_instance: dict[str, Any] | str | Path,
) -> dict[str, Any]:
    """Score a PSO solution file using GA's solver.validate_solution."""
    if isinstance(ga_instance, (str, Path)):
        ga_instance = json.loads(Path(ga_instance).read_text(encoding='utf-8'))

    raw = json.loads(Path(pso_solution_path).read_text(encoding='utf-8'))
    best = raw.get('best_solution', raw)
    trips = best['trips']

    vehicles = ga_instance['vehicles']
    pso_groups = [[] for _ in vehicles]
    for t in trips:
        v_idx = t['vehicle_index']
        pso_groups[v_idx].append([int(c) for c in t['customers']])

    # Schedule through GA solver
    scheduled_trips = solver.schedule(pso_groups, ga_instance, vehicles)

    # Validate against instance (using witness horizon if instance has no horizon)
    model = dict(ga_instance.get('model', {}))
    inst_for_val = dict(ga_instance, model=model)
    validation = solver.validate_solution(inst_for_val, scheduled_trips)

    cost = validation['cost']
    reported_cost = best.get('true_cost_eur')
    diff = abs(cost['real_cost_eur'] - reported_cost) if reported_cost is not None else None

    return {
        'method': best.get('method', 'pso'),
        'pso_reported_true_cost_eur': reported_cost,
        'ga_real_cost_eur': cost['real_cost_eur'],
        'ga_penalty_eur': cost['penalty_eur'],
        'ga_total_eur': cost['total_eur'],
        'cost_difference': diff,
        'agreement_within_1_cent': diff < 0.01 if diff is not None else None,
        'feasible': validation['feasible'],
        'trips': validation['trips'],
        'distance_km': validation['distance_km'],
        'fuel_litres': validation['fuel_litres'],
    }


def evaluate_ga_with_pso(
    ga_solution_path: str | Path,
    pso_dataset_dir: str | Path,
    pso_repo_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Score a GA solution file using PSO's cost, day_metrics, and check_solution."""
    _ensure_pso_imported(pso_repo_dir)
    import numpy as np
    from src.cost import DEFAULT_WEIGHTS, day_metrics, trip_metrics
    from src.data_loader import ProblemData, load_problem
    from src.decoder import Solution, TripPlan, check_solution

    raw = json.loads(Path(ga_solution_path).read_text(encoding='utf-8'))
    data = load_problem(str(pso_dataset_dir))

    best = raw.get('best', raw)
    transports = best.get('transports', raw.get('transports', []))
    if not transports and 'reference_transports' in raw:
        transports = raw['reference_transports']

    trip_plans: list[TripPlan] = []
    for t in transports:
        k = t['vehicle']
        custs = [int(c) for c in t['customers']]
        tm = trip_metrics(data, k, custs, DEFAULT_WEIGHTS)
        tp = TripPlan(
            vehicle_index=k,
            vehicle_id=data.vehicles[k].vehicle_id,
            customers=custs,
            metrics=tm,
        )
        trip_plans.append(tp)

    V = data.n_vehicles
    v_times = np.zeros(V, dtype=np.float64)
    v_max_ret = np.zeros(V, dtype=np.float64)

    for tp in trip_plans:
        k = tp.vehicle_index
        v_times[k] += tp.metrics.total_min
        ret_min = float(data.distance[tp.customers[-1], 0] / data.vehicles[k].avg_speed_kmh * 60.0)
        v_max_ret[k] = max(v_max_ret[k], ret_min)

    days = [
        day_metrics(data, k, v_times[k], v_max_ret[k], DEFAULT_WEIGHTS)
        for k in range(V)
    ]
    vehicle_overtime_min = np.array([d.beyond_shift_min for d in days])
    vehicle_overtime_cost = np.array([d.extra_cost for d in days])
    day_overtime_cost = float(vehicle_overtime_cost.sum())
    day_penalty = float(sum(d.penalty for d in days))

    base_cost = sum(t.metrics.base_cost_eur for t in trip_plans)
    true_cost = base_cost + day_overtime_cost
    trip_penalties = sum(t.metrics.penalty for t in trip_plans)
    total_penalty = trip_penalties + day_penalty
    total_dist = sum(t.metrics.distance_km for t in trip_plans)
    total_time = sum(t.metrics.total_min for t in trip_plans)
    total_wt = sum(t.metrics.weight_kg for t in trip_plans)
    total_vol = sum(t.metrics.volume_m3 for t in trip_plans)

    pso_sol = Solution(
        trips=trip_plans,
        true_cost_eur=float(true_cost),
        penalty=float(total_penalty),
        objective=float(true_cost + total_penalty),
        feasible=(total_penalty <= 1e-7),
        total_distance_km=float(total_dist),
        total_time_min=float(total_time),
        total_weight_kg=float(total_wt),
        total_volume_m3=float(total_vol),
        vehicle_total_min=v_times,
        vehicle_overtime_min=vehicle_overtime_min,
        vehicle_overtime_cost=vehicle_overtime_cost,
        day_overtime_cost=day_overtime_cost,
        method=raw.get('method', 'ga'),
        vehicle_night_min=np.array([d.night_min for d in days]),
        vehicle_last_delivery_min=np.array([d.last_delivery_min for d in days]),
        vehicle_day_penalty=np.array([d.penalty for d in days]),
    )

    errors = check_solution(data, pso_sol)

    ga_cost = best.get('cost', {}).get('real_cost_eur') if isinstance(best.get('cost'), dict) else None
    if ga_cost is None and 'validation' in raw and 'cost' in raw['validation']:
        ga_cost = raw['validation']['cost'].get('real_cost_eur')

    diff = abs(true_cost - ga_cost) if ga_cost is not None else None

    return {
        'method': raw.get('method', 'ga'),
        'ga_reported_cost_eur': ga_cost,
        'pso_true_cost_eur': round(float(true_cost), 4),
        'pso_penalty': round(float(total_penalty), 4),
        'pso_day_penalty': round(float(day_penalty), 4),
        'pso_longest_day_h': round(float(pso_sol.longest_day_min) / 60.0, 2),
        'pso_overtime_h': round(float(vehicle_overtime_min.sum()) / 60.0, 2),
        'check_errors': errors,
        'cost_difference': diff,
        'agreement_within_1_cent': diff < 0.01 if diff is not None else None,
        'pso_feasible': pso_sol.feasible and len(errors) == 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pso-repo', type=Path, help='path to industrial-transport repository')
    sub = parser.add_subparsers(dest='command', required=True)

    p1 = sub.add_parser('pso-to-ga', help='Evaluate PSO plan with GA validator')
    p1.add_argument('--pso-solution', type=Path, required=True)
    p1.add_argument('--ga-instance', type=Path, required=True)

    p2 = sub.add_parser('ga-to-pso', help='Evaluate GA plan with PSO validator')
    p2.add_argument('--ga-solution', type=Path, required=True)
    p2.add_argument('--pso-dataset', type=Path, required=True)

    args = parser.parse_args()
    if args.command == 'pso-to-ga':
        res = evaluate_pso_with_ga(args.pso_solution, args.ga_instance)
        print(json.dumps(res, indent=2))
    elif args.command == 'ga-to-pso':
        res = evaluate_ga_with_pso(args.ga_solution, args.pso_dataset, pso_repo_dir=args.pso_repo)
        print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
