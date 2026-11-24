"""Bounded improvement of the feasible GA incumbent with inter-trip moves."""

from itertools import combinations

from solver import (EPS, SolutionViolation, candidate_from_trips, evaluate_costs,
                    schedule, soft_min_stops, stop_limits, validate_solution)


def move_indices(groups, instance, vehicles, volume_buffer, operator, screened_pairs):
    hard_minimum, maximum = stop_limits(instance)
    minimum = soft_min_stops(instance)
    routes = [(vehicle, trip) for vehicle, trips in enumerate(groups) for trip in range(len(trips))]
    sizes = {key: len(groups[key[0]][key[1]]) for key in routes}
    customers = instance['customers']
    distances = instance['distance_matrix_m']
    anchors = {key: groups[key[0]][key[1]][0] for key in routes}
    volumes = [[customers[node]['volume_m3'] for node in groups[k][t]] for k, t in routes]
    smallest = {key: min(load) for key, load in zip(routes, volumes)}
    spare = {key: vehicles[key[0]]['volume_m3']*(1-volume_buffer)-sum(load)
             for key, load in zip(routes, volumes)}

    def shortfall(size):
        return max(0, minimum - size) if size else 0

    def short_involved(pair):
        return not any(sizes[key] < minimum for key in pair)

    def pair_distance(pair):
        a, b = map(anchors.get, pair)
        return distances[a][b]+distances[b][a]

    pairs = list(combinations(routes, 2))
    if operator == 'relocate':
        pairs += [(target, source) for source, target in pairs]
        eligible = []
        for a, b in pairs:
            if sizes[b] >= maximum:
                screened_pairs['max_stops'] += 1
            elif smallest[a] > spare[b]+EPS:
                screened_pairs['usable_volume'] += 1
            elif 1 < sizes[a] <= hard_minimum:
                screened_pairs['min_stops'] += 1
            else:
                eligible.append((a,b))
        pairs = eligible

        def priority(pair):
            a, b = map(sizes.get, pair)
            delta = shortfall(a - 1) + shortfall(b + 1) - shortfall(a) - shortfall(b)
            short_trips_delta = sum(shortfall(size)>0 for size in (a-1,b+1))-sum(
                shortfall(size)>0 for size in (a,b))
            source, target = pair
            return short_trips_delta, delta, short_involved(pair), source[0]!=target[0], pair_distance(pair)

        pairs.sort(key=priority)
    else:
        pairs.sort(key=lambda pair:(short_involved(pair),pair[0][0]!=pair[1][0],pair_distance(pair)))
    for a, b in pairs:
        for i in range(sizes[a]):
            for j in range(sizes[b] + (operator == 'relocate')):
                yield a, i, b, j


class CrossTripSearch:
    def __init__(self, instance, volume_buffer, cost_overrides, operators):
        self.instance = instance
        self.volume_buffer = instance.get('model', {}).get('volume_buffer', 0.) if volume_buffer is None else volume_buffer
        self.cost_overrides = cost_overrides
        self.operators = operators
        self.counts = {op: dict(attempted=0, valid=0, accepted=0) for op in operators}
        self.relocate_rejections = dict.fromkeys(
            ('payload','usable_volume','max_stops','workday_horizon','coverage',
             'empty_trip','min_stops','no_improvement','other_validation'), 0)
        self.relocate_screened_route_pairs = dict.fromkeys(('max_stops','usable_volume','min_stops'), 0)
        self.incumbent = None
        self.next_operator = 0

    @property
    def trials(self):
        return sum(count['attempted'] for count in self.counts.values())

    def reset(self, candidate):
        self.incumbent = candidate
        self.groups = [[] for _ in candidate['fleet']]
        self.vehicle_trips = [[] for _ in candidate['fleet']]
        for trip in candidate['transports']:
            vehicle = trip['vehicle']
            self.groups[vehicle].append(trip['customers'])
            self.vehicle_trips[vehicle].append(trip)
        self.moves = {op: move_indices(self.groups,self.instance,candidate['fleet'],self.volume_buffer,op,
                                      self.relocate_screened_route_pairs)
                      for op in self.operators}

    def try_move(self, operator, move):
        (a, ta), i, (b, tb), j = move
        affected = {a, b}
        updated = [[] for _ in self.groups]
        for k in affected:
            updated[k] = [route[:] for route in self.groups[k]]
        source, target = updated[a][ta], updated[b][tb]
        if operator == 'relocate':
            target.insert(j, source.pop(i))
            if not source:
                updated[a].pop(ta)
        else:
            source[i], target[j] = target[j], source[i]

        current = self.incumbent
        vehicles = current['fleet']
        # The schedule starts each affected vehicle at minute zero and runs
        # every trip in order, including those whose routes were untouched.
        fresh = [[] for _ in vehicles]
        for trip in schedule(updated, self.instance, vehicles):
            fresh[trip['vehicle']].append(trip)
        trips = [trip for k, old in enumerate(self.vehicle_trips)
                 for trip in (fresh[k] if k in affected else old)]
        self.counts[operator]['attempted'] += 1
        try:
            validation = validate_solution(self.instance, trips, vehicles, self.volume_buffer, self.cost_overrides)
        except ValueError as exc:
            # The validator exits on the first hard violation. Still reprice
            # the proposed workdays, keeping their scores out of selection.
            evaluate_costs(trips, vehicles, self.instance, self.cost_overrides)
            if operator == 'relocate':
                reason = exc.reason if isinstance(exc,SolutionViolation) else 'other_validation'
                self.relocate_rejections[reason] += 1
            return None

        self.counts[operator]['valid'] += 1
        cost = validation['cost']
        if cost['total_eur'] >= current['total_eur']:
            if operator == 'relocate':
                self.relocate_rejections['no_improvement'] += 1
            return None
        self.counts[operator]['accepted'] += 1
        return dict(candidate_from_trips(trips, vehicles, current['genome'][2], self.instance,
                                         self.cost_overrides, cost), horizon_excess_minutes=0.)

    def improve(self, candidate, limit):
        if self.incumbent is not candidate:
            self.reset(candidate)
        for _ in range(limit):
            for _ in self.operators:
                operator = self.operators[self.next_operator]
                self.next_operator = (self.next_operator + 1) % len(self.operators)
                move = next(self.moves[operator], None)
                if move is not None:
                    break
            else:
                break
            improved = self.try_move(operator, move)
            if improved is not None:
                self.reset(improved)
        return self.incumbent
