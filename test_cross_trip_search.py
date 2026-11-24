import unittest
from unittest.mock import patch

from cross_trip_search import CrossTripSearch
from solver import SolutionViolation, decoded_groups, evaluate_costs, schedule, solve, validate_solution
from test_solver import ready


class CrossTripSearchTests(unittest.TestCase):
    def candidate(self, work, groups, minimum=1, demand=1):
        instance = ready()
        instance['model'].update(time_horizon_minutes=960, min_stops_per_trip=minimum)
        size = len(work)+1
        instance['distance_matrix_m'] = [[0]*size for _ in range(size)]
        instance['duration_matrix_s'] = [[0]*size for _ in range(size)]
        instance['customers'] = [
            dict(id=i, weight_kg=demand*(i>0), volume_m3=demand*(i>0), service_minutes=minutes)
            for i, minutes in enumerate([0]+work)
        ]
        original = decoded_groups(groups, instance['vehicles'], [0,1,2,0,1], instance, None)
        validate_solution(instance, original['transports'])
        return instance, original

    def test_cross_vehicle_relocate_reschedules_later_trips_and_wages(self):
        instance, original = self.candidate([60,480,100,60,60], [[[1],[2]],[[3,4],[5]],[],[],[]])
        search = CrossTripSearch(instance, None, None, ['relocate'])
        search.reset(original)
        moved = search.try_move('relocate', ((0,0),0,(1,0),0))
        self.assertIsNotNone(moved)
        trips = moved['transports']
        self.assertEqual([t['customers'] for t in trips], [[2],[1,3,4],[5]])
        self.assertEqual([t['start_minutes'] for t in trips], [0,0,220])
        self.assertEqual([t['finish_minutes'] for t in trips], [480,220,280])
        self.assertEqual(moved['cost']['overtime_hours'], 0)
        self.assertAlmostEqual(original['total_eur']-moved['total_eur'], 20)
        self.assertEqual(original['transports'][0]['customers'], [1])

    def test_cross_vehicle_swap_reschedules_both_days(self):
        instance, original = self.candidate([120,480,30,60], [[[1],[2]],[[3],[4]],[],[],[]])
        search = CrossTripSearch(instance, None, None, ['swap'])
        search.reset(original)
        moved = search.try_move('swap', ((0,0),0,(1,0),0))
        self.assertIsNotNone(moved)
        self.assertEqual([t['customers'] for t in moved['transports']], [[3],[2],[1],[4]])
        self.assertEqual([t['start_minutes'] for t in moved['transports']], [0,30,0,120])
        self.assertEqual(moved['cost']['overtime_hours'], 0.5)
        self.assertAlmostEqual(original['total_eur']-moved['total_eur'], 30)

    def test_same_vehicle_relocate_removes_short_trip(self):
        instance, original = self.candidate([60,60,60], [[[1],[2,3]],[],[],[],[]], minimum=10)
        search = CrossTripSearch(instance, None, None, ['relocate'])
        search.reset(original)
        moved = search.try_move('relocate', ((0,0),0,(0,1),2))
        self.assertIsNotNone(moved)
        self.assertEqual([t['customers'] for t in moved['transports']], [[2,3,1]])
        self.assertEqual(original['total_eur']-moved['total_eur'], 20_000)

    def test_relocate_accepts_cross_vehicle_move_that_reduces_soft_penalty(self):
        groups = [[[1]], [list(range(2,10))], [], [], []]
        instance, original = self.candidate([20]*9, groups, minimum=10, demand=0.25)
        instance['model'].update(volume_buffer=0.1, max_stops_per_trip=50)
        validate_solution(instance, original['transports'])
        search = CrossTripSearch(instance, None, None, ['relocate'])
        moved = search.improve(original, 1)
        checked = validate_solution(instance, moved['transports'])
        self.assertEqual(checked['finish_minutes_by_vehicle'], [0,180,0,0,0])
        self.assertEqual(len(moved['transports']), 1)
        self.assertEqual(moved['transports'][0]['customers'], [1,*range(2,10)])
        self.assertEqual(original['cost']['penalty_eur'], 22_000)
        self.assertEqual(checked['cost']['penalty_eur'], 2_000)
        self.assertLess(moved['total_eur'], original['total_eur'])
        self.assertEqual(search.counts['relocate'], dict(attempted=1,valid=1,accepted=1))
        self.assertEqual(sum(search.relocate_rejections.values()), 0)

    def test_rejects_cheaper_move_when_following_trip_would_pass_midnight(self):
        instance, original = self.candidate([100,100,400,500], [[[1],[2]],[[3],[4]],[],[],[]], minimum=10)
        search = CrossTripSearch(instance, None, None, ['relocate'])
        search.reset(original)
        with patch('cross_trip_search.evaluate_costs', wraps=evaluate_costs) as score:
            self.assertIsNone(search.try_move('relocate', ((0,0),0,(1,0),0)))
        score.assert_called_once()
        self.assertEqual(score.call_args.args[0][-1]['finish_minutes'], 1000)
        self.assertEqual(search.counts['relocate'], dict(attempted=1,valid=0,accepted=0))
        self.assertEqual(search.relocate_rejections['workday_horizon'], 1)

    def test_relocate_distinguishes_payload_and_volume_rejections(self):
        for field, reason in [('weight_kg','payload'), ('volume_m3','usable_volume')]:
            with self.subTest(reason=reason):
                instance, original = self.candidate([20]*3, [[[1]],[[2,3]],[],[],[]])
                for customer in instance['customers'][1:]:
                    customer[field] = 3
                validate_solution(instance, original['transports'])
                search = CrossTripSearch(instance, None, None, ['relocate'])
                search.reset(original)
                self.assertIsNone(search.try_move('relocate', ((0,0),0,(1,0),0)))
                self.assertEqual(search.relocate_rejections[reason], 1)

    def test_relocate_reports_max_stops_screening_separately(self):
        instance, original = self.candidate([1]*51, [[[1]],[list(range(2,52))],[],[],[]], demand=0.05)
        search = CrossTripSearch(instance, None, None, ['relocate'])
        search.reset(original)
        next(search.moves['relocate'])
        self.assertEqual(search.relocate_screened_route_pairs['max_stops'], 1)
        self.assertEqual(search.trials, 0)
        self.assertIsNone(search.try_move('relocate', ((0,0),0,(1,0),0)))
        self.assertEqual(search.relocate_rejections['max_stops'], 1)

    def test_coverage_and_empty_trip_have_distinct_validator_reasons(self):
        instance, _ = self.candidate([20]*3, [[[1]],[[2,3]],[],[],[]])
        for route, reason in [([2,2,3],'coverage'), ([], 'empty_trip')]:
            with self.subTest(reason=reason):
                trips = schedule([[route],[],[],[],[]], instance)
                with self.assertRaises(SolutionViolation) as error:
                    validate_solution(instance, trips)
                self.assertEqual(error.exception.reason, reason)

    def test_feasible_tie_does_not_replace_incumbent(self):
        instance, original = self.candidate([60,60], [[[1]],[[2]],[],[],[]])
        search = CrossTripSearch(instance, None, None, ['relocate'])
        self.assertIs(search.improve(original, 10), original)
        self.assertEqual(search.counts['relocate'], dict(attempted=4,valid=4,accepted=0))
        self.assertEqual(search.relocate_rejections['no_improvement'], 4)

    def test_operator_toggles_and_combined_budget(self):
        instance, original = self.candidate([300]*6, [[[1,2,3]],[[4,5,6]],[],[],[]], minimum=10)
        for operator in ('relocate','swap'):
            with self.subTest(operator=operator):
                result = solve(instance, objective='cost', population=4, generations=3,
                               initial_transports=original['transports'], evaluation_budget=9,
                               **{operator:True})
                self.assertEqual(set(result['cross_trip_counts']), {operator})
                self.assertGreater(result['local_trials'], 0)
                self.assertEqual(result['combined_evaluations'], 9)
                self.assertEqual(result['evaluations']+result['local_trials'], 9)
                self.assertTrue(result['validation']['feasible'])


if __name__ == '__main__':
    unittest.main()
