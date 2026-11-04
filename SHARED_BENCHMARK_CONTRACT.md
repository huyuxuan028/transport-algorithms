# Shared benchmark contract: review proposal

Source: the PSO-team CSV dataset, imported once as `data/shared_pso_250.json`.
It contains 250 customer records and a depot, with five fixed vehicles:
two Caddy, two Sprinter and one MAN. Preserve customer IDs, orders, item
dimensions, service times, capacities, wages, maintenance and fuel parameters.

The source distance matrix is haversine times 1.3. The road extension is
`data/shared_pso_250_road.json`, built from the original `coordinates_lonlat`.
Both teams must freeze and use exactly the same road file and checksum before
reporting a GA-versus-PSO comparison. Adopting the same addresses alone is insufficient.

## Current shared policy: PR #8 stop and cost rule

The shared benchmark uses a fixed available fleet (idle vehicles permitted),
indivisible orders, exact-once delivery, depot return on each trip, sequential
nonoverlapping trips, payload and aggregate volume with 10% reserve, loading
plus unloading as work, normal wages for eight hours then double wage.

- Minimum 10 customers per trip is SOFT. A nonempty trip with fewer than 10
  customers is allowed, with EUR 2,000 per missing customer. An unused vehicle
  does not create a trip or a minimum-stop penalty.
- Maximum 50 customers per trip is HARD. A 51-customer trip is infeasible;
  the bound must be enforced by both the decoder/Split and solution validation.
- `real_cost_eur = fuel_eur + wage_eur + maintenance_eur` reports the estimated
  operational monetary cost, including overtime wages and excluding penalties.
- `penalty_eur = 2000 * sum(max(0, 10 - stops_in_trip))`, summed over trips.
- `total_eur = real_cost_eur + penalty_eur` is the optimization score minimized
  by the cost objective. Report all three fields separately.
- `true_cost_eur_ours` in evaluator comparisons means `real_cost_eur`, never
  the penalty-inclusive score. If `objective_eur` is used as a reporting alias,
  it equals `total_eur`.

For example: one 8-customer trip incurs EUR 4,000 of minimum-stop penalty;
its operational cost is unchanged by that accounting penalty. This EUR 2,000
coefficient is the shared setting `model.min_stops_penalty_eur_per_customer`,
not an assumption that all legacy instances have that default.

This is the agreed rule requested for alignment with PR #8. Integrating/rebasing
code must preserve the cost separation AND the hard maximum. Documentation alone
does not establish that either is implemented; verify the merged decoder and
validator, especially the maximum in soft-minimum mode. An option that makes
both 10 and 50 hard is a separate experimental scenario, not the shared default.

## Historical road experiments: hard minimum and maximum

The previously recorded 25 runs used a hard 10–50 policy. They are historical
experiments under a different feasible set, not runs of the PR #8 soft-minimum
policy. Their unchanged costs and convergence traces must not be relabeled as
new-policy results. After code integration, rerun and record the effective stop
policy, EUR 2,000 coefficient, input checksum, real cost, penalty and total score.
The original source model was preserved; the old runner recorded its hard-mode
override. Those artifacts do not prove alignment with the current shared rule.

No geometric packing, release times, time windows, daily/weekly horizon, rest
scheduling, live traffic, turn-restriction relations or HGV-specific clearance
is implemented. These exclusions require team/supervisor agreement; this document
is a proposal and evidence record, not proof of that agreement.

Neutral initialization is independent of the PSO published best plan. The published
PSO result is evaluator-audit data only and its old cost must not be compared to
a road-based GA cost. Run PSO again on the identical road matrices.

Budget protocol: seeds 0–4, population 32, 80 generations, report ACTUAL evaluations
including feasibility fallback construction, runtime, feasibility, overtime,
maximum vehicle span and convergence. The historical hard-10–50 ablations had 2,433 evaluations
each. These counts are not a claim that new-policy experiments have been run.
This is an internal GA study; the PSO team has not yet executed this protocol.

Local graph audit: all 251 locations retained; two locations require explicit
reachable-component snapping (IDs 109 and 237; 78.63m and 81.18m). Maximum snap
across all locations is 114.47m. These address-to-vertex offsets are not drivable
legs and are excluded from routing costs. Both teams must accept the same snapping
policy. Do not silently move, delete or regenerate a customer to make a graph work.
