# Initial algorithm experiments

Shared Budapest addresses / local OSM graph. 5 seeds, population 32, 80 generations. Actual candidate evaluations are recorded per run; hard-mode fallback construction can add evaluations. Common decoder and initial witness. Random search also uses local search. Ablations change one mechanism, but RNG trajectories also change; no statistical significance claim. Feasible means only the explicitly implemented constraints. Stop-count mode: hard

| Variant | Mean cost EUR | SD | Best | Mean seconds | Feasible |
|---|---:|---:|---:|---:|---:|
| random_search | 2101.73 | 0.00 | 2101.73 | 0.58 | 5/5 |
| ga | 1944.07 | 10.79 | 1926.69 | 6.56 | 5/5 |
| ga_unseeded | 1941.61 | 19.86 | 1911.61 | 6.32 | 5/5 |
| ga_no_local_search | 2144.79 | 8.70 | 2132.62 | 3.86 | 5/5 |
| ga_no_order_crossover | 1939.14 | 22.51 | 1916.23 | 6.08 | 5/5 |

## Interpretation

One shared instance only; no certified optimum, optimality gap or significance
claim. All configurations used 2,433 candidate evaluations, including one extra
hard-feasible initialization attempt. This is evaluation-count matching, not
equal runtime. Random search and seeded GA share the same decoder, local search
and initialization; random search retained the initial feasible seed in all runs.

The main GA improves over the random reference by approximately 7.50% in mean cost.
Removing local search worsens mean cost. Neither NN seeding nor OX has a demonstrated
mean benefit on this hard-stop instance: their ablations are slightly cheaper.
A large portion of initialization is infeasible under hard stop counts, so the
conservative single-large-vehicle fallback dominates the starting point. That is
a design weakness to address, not a successful justification of every operator.

Best main GA: seed 1, EUR 1,926.692, distance 582.737km, seven trips, three used
vehicles out of five available, zero below/above stop-bound trips. Overtime is
43.1685 vehicle-hours. The longest vehicle work span is 51.17 hours. This is valid
only in the explicitly unbounded-horizon model, NOT a practical single-day plan.
Hard 10–50 bounds are the selected experimental policy, pending joint confirmation.

## Data and road audit

All 250 customer demands, item records, original lon/lat, vehicles and cost/service
parameters match Subhan's shared input. The graph covers all shared Budapest
locations; no delivery points were randomly resampled. There are 229,754 road
vertices and 222,862 in the depot's mutually reachable component. Every pair
in the 251x251 matrices is finite; 30,902 unordered distance pairs differ by
more than one metre between directions. Five full matrix rows were recomputed
against the graph and matched in distance and duration.

Road-file SHA256: `4560322db5a3ca30c5778bc4cf97e161c1daafa31f24b3d49cde3ddc2512b6e4`.
Raw-extract SHA256: `302481dc96268e15871692862a3d274921c1cf1ae81dcb0446b3fa51b0828376`.
Extract bbox (west,south,east,north): 18.91,47.36,19.26,47.64.
Two explicit reachable-component resnaps: IDs 109/237, offsets 78.63m / 81.18m.
Maximum vertex-snap offset:114.47m. These offsets are not billed as road legs.

Times are static road-class assumptions, optionally capped by numeric maxspeed
tags. One-way and basic motor access are modeled; turn relations, truck-specific
clearance, parking/unloading access and traffic are not. Finite boundaries may
exclude better routes; connectivity alone does not prove global shortest paths.
These results are local OSM calculations, not an executed ORS experiment.

## Shared comparison and reproducibility

The imported `data/shared_pso_250.json` contains the original approximate distance
matrix; `data/shared_pso_250_road.json` is the frozen road extension. The PSO team's
old published cost belongs to the approximate matrix, so it is NOT included as
a competitor here. Both teams need to run the same road extension first.

Raw extracts, road matrices, generated maps and full runs are distributed as
generated benchmark artifacts, outside code PR #5. Commands live in
SHARED_ROAD_WORKFLOW.md. Do not mix old Keleti figures into this results section.
