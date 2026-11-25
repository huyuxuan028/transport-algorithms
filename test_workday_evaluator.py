"""Controlled one-rule-at-a-time checks for the shared workday evaluator."""

import copy
import json
import unittest
from unittest.mock import patch

from solver import make_fleet, schedule, solve, validate_solution
from test_solver import ready


def evaluator_cases():
    instance = ready()
    for vehicle in instance['vehicle_types']:
        vehicle.update(payload_kg=100, volume_m3=100)
    instance['vehicles'] = make_fleet(instance, [0, 1, 2, 0, 1])
    instance['model'].update(time_horizon_minutes=960, volume_buffer=0.1,
                             min_stops_per_trip=10, max_stops_per_trip=50)
    instance['customers'] = [
        {'id': i, 'weight_kg': int(i > 0), 'volume_m3': int(i > 0), 'service_minutes': int(i > 0)}
        for i in range(71)
    ]
    instance['distance_matrix_m'] = [[1000 * (i != j) for j in range(71)] for i in range(71)]
    instance['duration_matrix_s'] = [[60 * (i != j) for j in range(71)] for i in range(71)]
    baseline = [[list(range(1, 51))], [list(range(51, 71))], [], [], []]
    cases = [
        ('baseline', True, 0, None),
        ('payload', False, None, 'Overloaded trip'),
        ('usable_volume', False, None, 'Overloaded trip'),
        ('eight_stops', True, 4000, None),
        ('fifty_one_stops', False, None, 'Hard stop-count violation'),
        ('missing_customer', False, None, 'Missing or duplicated customers'),
        ('duplicate_customer', False, None, 'Missing or duplicated customers'),
        ('cumulative_961_minutes', False, None, 'Vehicle exceeds time_horizon_minutes'),
    ]
    report = []
    for name, feasible, penalty, error in cases:
        case = copy.deepcopy(instance)
        groups = copy.deepcopy(baseline)
        if name == 'payload':
            case['customers'][1]['weight_kg'] = 52  # 101 kg against 100 kg
        elif name == 'usable_volume':
            case['customers'][1]['volume_m3'] = 42  # 91 m³ against 90 m³ usable
        elif name == 'eight_stops':
            groups[0] = [list(range(1, 43)), list(range(43, 51))]
        elif name == 'fifty_one_stops':
            groups[0][0].append(groups[1][0].pop(0))
        elif name == 'missing_customer':
            groups[1][0].pop()
        elif name == 'duplicate_customer':
            groups[1][0].append(1)
        elif name == 'cumulative_961_minutes':
            groups[0] = [list(range(1, 26)), list(range(26, 51))]
            case['customers'][1]['service_minutes'] += 859  # 910 + 51 minutes
        trips = schedule(groups, case)
        expected = {'feasible': feasible, 'penalty_eur': penalty, 'error': error}
        try:
            validation = validate_solution(case, trips)
        except ValueError as exc:
            actual = {'feasible': False, 'penalty_eur': None, 'error': str(exc)}
        else:
            actual = {'feasible': True, 'penalty_eur': validation['cost']['penalty_eur'], 'error': None}
        report.append({'case': name, 'expected': expected, 'actual': actual,
                       'max_vehicle_minutes': max(t['finish_minutes'] for t in trips)})
    return report


class WorkdayEvaluatorTests(unittest.TestCase):
    def test_controlled_rule_violations(self):
        for row in evaluator_cases():
            with self.subTest(case=row['case']):
                self.assertEqual(row['actual'], row['expected'])

    def test_unseeded_search_excludes_reference_and_fallback(self):
        instance = ready()
        del instance['reference_transports']
        instance['model']['time_horizon_minutes'] = 0.00001
        with patch('solver.rebalance_workday', side_effect=AssertionError('Seed repair must be disabled')):
            result = solve(instance, heuristic_seed=False, population=4, generations=3,
                           evaluation_budget=7, audit=True)
        self.assertIsNone(result['generated_witness'])
        self.assertIsNone(result['baseline_decoded'])
        self.assertEqual(len(result['initial_random_audit']), 4)
        self.assertEqual(result['history'][0]['evaluations'], 4)
        self.assertEqual(result['evaluations'], 7)
        self.assertEqual(result['history'][-1]['population_size'], 4)
        self.assertFalse(result['validation']['feasible'])
        self.assertIsNone(result['best'])

    def test_horizon_penalty_search_returns_a_validated_plan_inside_the_workday(self):
        instance = ready()
        instance['model'].update(time_horizon_minutes=960, min_stops_per_trip=1, max_stops_per_trip=2)
        instance['duration_matrix_s'] = [[0 if a == b else 1200 for b in range(5)] for a in range(5)]
        for customer in instance['customers'][1:]:
            customer['service_minutes'] = 210
        instance['customers'][4]['service_minutes'] += 1  # the reference plan now ends at minute 961
        instance['reference_transports'] = schedule([[[1, 2], [3, 4]], [], [], [], []], instance)
        result = solve(instance, seed=0, population=12, generations=5, objective='cost',
                       horizon_penalty_eur_per_minute=5.0)
        self.assertEqual(result['horizon_penalty_eur_per_minute'], 5.0)
        self.assertTrue(result['validation']['feasible'])
        self.assertLessEqual(max(result['validation']['finish_minutes_by_vehicle']), 960)
        objectives = [point['objective'] for point in result['history'] if point['objective'] is not None]
        self.assertEqual(objectives, sorted(objectives, reverse=True))  # incumbent never gets worse

    def test_horizon_penalty_requires_cost_objective_and_positive_rate(self):
        instance = ready()
        for objective, rate in [('distance', 5.0), ('cost', 0), ('cost', float('inf'))]:
            with self.subTest(objective=objective, rate=rate), self.assertRaisesRegex(ValueError, 'Horizon penalty'):
                solve(instance, population=4, generations=1, objective=objective,
                      horizon_penalty_eur_per_minute=rate)


if __name__ == '__main__':
    print(json.dumps(evaluator_cases(), indent=2))
