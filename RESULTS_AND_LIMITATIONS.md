# Shared-road results and limitations

## Current study: soft minimum, hard maximum

Subhan ran the experiments on branch `feature/Subhan/soft-stop-repair`, frozen
at commit `48f3367693ea36c53a0964fad47f90f9ec3af1f4`. HU checked the reported plans with that commit's
validator and independently rescheduled the fixed PSO-team reference plan.
These checks re-evaluate existing results; they are not fresh GA or PSO searches.

Input: `data/shared_pso_250_road.json`, 250 customers and five fixed physical
vehicles. The experiment input was the original road file with SHA-256
`4560322db5a3ca30c5778bc4cf97e161c1daafa31f24b3d49cde3ddc2512b6e4`. Seeds 0–4, population 32, 200 generations, 6,032 candidate evaluations
per run, `stop_count_mode=soft`. Minimum 10 is soft at EUR 2,000 per missing
customer; maximum 50 is hard. The pilot has 30 runs: three objectives, two
methods and five seeds. The table below is ONLY the five cost-objective GA runs.

`real_cost_eur = fuel_eur + wage_eur + maintenance_eur`;
`total_eur = real_cost_eur + penalty_eur`. Penalty is a search score component,
not money charged for operating the vehicles. All five final cost-GA plans
have zero minimum-stop penalty and no trip exceeding 50.

| Seed | Real cost EUR | Penalty EUR | Total score EUR | Overtime h |
|---|---:|---:|---:|---:|
| 0 | 1480.1810 | 0.0000 | 1480.1810 | 24.9487 |
| 1 | 1461.0733 | 0.0000 | 1461.0733 | 24.7383 |
| 2 | 1478.2660 | 0.0000 | 1478.2660 | 25.9463 |
| 3 | 1473.6202 | 0.0000 | 1473.6202 | 25.2847 |
| 4 | 1473.8275 | 0.0000 | 1473.8275 | 24.7334 |

Mean real cost and mean total score: **EUR 1,473.3936**. Best: **EUR 1,461.0733**
(seed 1). Sample standard deviation: **EUR 7.4471**. Reported rounded values are
EUR 1,473.39, EUR 1,461.07 and EUR 7.45. Mean recorded runtime is 18.4126seconds
on Subhan's reported machine, not a cross-machine timing comparison.

Best cost-GA plan: 15 trips, all five vehicles used, 733.4073km, overtime 24.7383
vehicle-hours, maximum vehicle work span 18.6939hours. This remains an
unrestricted-horizon schedule, not a validated realistic single-day plan.

The same pilot's cost-objective random-search mean is EUR 1,662.5519. Both methods
receive the same decoder, repair/local search and candidate-evaluation budget;
wall-clock budgets differ. This is a stronger constructive/repair baseline,
not pure random routing. No isolated ablation of the new repair mechanisms has
been performed, so do not attribute all improvement to one operator.

## Fixed PSO-team reference plan re-evaluated on road matrices

The original embedded reference plan still contained approximate-matrix trip
metrics. Its vehicle assignments and within-trip customer orders are now unchanged
but passed through `solver.schedule` on the road matrices, then through validation.
The resulting values are:

| Metric | Value |
|---|---:|
| Real operating cost EUR |1472.0597|
| Penalty EUR |0.0000|
| Total score EUR |1472.0597|
| Overtime vehicle-hours |28.4723|
| Distance km |859.8231|
| Trips |15|
| Maximum customers in a trip |36|

This is a **re-evaluation of a fixed published plan**, not a new PSO optimization
on the road data and not a multi-seed PSO benchmark. The best GA plan is
EUR 10.9864 (about EUR 10.99) cheaper than this fixed reference. No optimality gap
or general superiority over PSO is established. The original reported
EUR 1,177.2974 approximate-matrix cost is retained ONLY as historical provenance;
`pso_reference_solution.true_cost_eur_ours` now means road real cost EUR 1,472.0597.

## File revision, hashes and provenance

The reference-audit-only revised road file has SHA-256
`6d794dff4a03cebb1f9127796209fa1f263450a780ce76ade9c26244b6a2676c`. Only the top-level `pso_reference_solution` block changes: its
trip metrics, road costs and explanatory provenance are refreshed. Orders,
vehicles, original coordinates, neutral GA `reference_transports`, models,
distance matrix, duration matrix and road geometry are unchanged.

Keep **both** hashes: `4560322db5a3ca30c5778bc4cf97e161c1daafa31f24b3d49cde3ddc2512b6e4` identifies Subhan's actual experiment input;
`6d794dff4a03cebb1f9127796209fa1f263450a780ce76ade9c26244b6a2676c` identifies the corrected attachment. These are different whole-file
hashes even though their optimization inputs are identical. Do not retroactively
replace the recorded experiment-input hash. Audit evidence records canonical
matrix hashes and the unchanged routing inputs.

Source artifacts (immutable commit links):
- [Pilot JSON](https://github.com/huyuxuan028/transport-algorithms/blob/48f3367693ea36c53a0964fad47f90f9ec3af1f4/results/shared_pso_250_road_pilot.json)
- [Selected solution](https://github.com/huyuxuan028/transport-algorithms/blob/48f3367693ea36c53a0964fad47f90f9ec3af1f4/results/solution.json)
- [Figures and benchmark table](https://github.com/huyuxuan028/transport-algorithms/blob/48f3367693ea36c53a0964fad47f90f9ec3af1f4/figures/shared_pso_250_road)
- [Solver implementation](https://github.com/huyuxuan028/transport-algorithms/blob/48f3367693ea36c53a0964fad47f90f9ec3af1f4/solver.py)

Pilot SHA-256: `b5f48a1c346e26ee1327ca575ca1dc93d1bb522cde0260cc7e53c69582e10bb8`.
All 30 pilot plans were revalidated against the original road matrices; their
reported costs match the evaluator. Histories are best-so-far nonincreasing.
This verifies saved artifacts, not an independent reproduction of the searches.

## Historical hard-10–50 study

The earlier study used five algorithm variants, five seeds, 32 individuals,
80 generations and typically 2,433 evaluations per run. Main-GA mean cost was
EUR 1,944.07; best EUR 1,926.69; best plan's longest vehicle span 51.17hours.
Those results remain historical under a different constraint/search configuration.
The new budget is larger and the decoder/repair changed, so this is not a
controlled estimate of the effect of relaxing the minimum alone.

## Remaining model and research limits

The OSM graph covers all shared coordinates, applies one-way/basic access tags,
and chooses estimated-time paths with matched distance/time. It omits turn
restriction relations and HGV-specific clearance; times are static assumptions,
not traffic measurements. Two addresses require audited reachable-component
resnapping (IDs 109/237, 78.63m/81.18m); maximum vertex offset 114.47m.
Offsets are not billed as drivable road legs. Finite boundaries may omit better
routes. All locations were retained; furniture orders are simulated shared inputs.

No geometric 3D packing, working-day/rest horizon, time windows or live traffic.
Do not claim the complete real-world problem is solved. The updated branch's
Split minimizes missing-customer count first and distance second, not the exact
finite monetary objective. Broader benchmarks, separate mechanism ablations,
load balancing and cost-aware decoding remain needed. The soft-repair algorithm
branch requires its own review/merge; documenting its results does not merge it.
