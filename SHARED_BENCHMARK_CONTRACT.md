# Shared benchmark contract: review proposal

Source: the PSO-team CSV dataset, imported once as `data/shared_pso_250.json`.
It contains 250 customer records and a depot, with five fixed vehicles:
two Caddy, two Sprinter and one MAN. Preserve customer IDs, orders, item
dimensions, service times, capacities, wages, maintenance and fuel parameters.

The source distance matrix is haversine times 1.3. The road extension is
`data/shared_pso_250_road.json`, built from the original `coordinates_lonlat`.
Both teams must freeze and use exactly the same road file and checksum before
reporting a GA-versus-PSO comparison. Adopting the same addresses alone is insufficient.

Current measured scenario: fixed available fleet (idle vehicles permitted),
indivisible orders, exact-once delivery, depot return on each trip, sequential
nonoverlapping trips, payload and aggregate volume with 10% reserve, loading
plus unloading as work, normal wages for eight hours then double wage.
Hard 10–50 customers per trip is the explicitly selected experimental policy.
The original source model is preserved; the experiment runner records the override.

No geometric packing, release times, time windows, daily/weekly horizon, rest
scheduling, live traffic, turn-restriction relations or HGV-specific clearance
is implemented. These exclusions require team/supervisor agreement; this document
is a proposal and evidence record, not proof of that agreement.

Neutral initialization is independent of the PSO published best plan. The published
PSO result is evaluator-audit data only and its old cost must not be compared to
a road-based GA cost. Run PSO again on the identical road matrices.

Budget protocol: seeds 0–4, population 32, 80 generations, report ACTUAL evaluations
including feasibility fallback construction, runtime, feasibility, overtime,
maximum vehicle span and convergence. The present ablations have 2,433 evaluations
each. This is an internal GA study; the PSO team has not yet executed this protocol.

Local graph audit: all 251 locations retained; two locations require explicit
reachable-component snapping (IDs 109 and 237; 78.63m and 81.18m). Maximum snap
across all locations is 114.47m. These address-to-vertex offsets are not drivable
legs and are excluded from routing costs. Both teams must accept the same snapping
policy. Do not silently move, delete or regenerate a customer to make a graph work.
