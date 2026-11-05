# Intentional design and evidence

## Shared stop policy and cost semantics (PR #8 and soft-stop-repair integration)

Minimum 10 is soft: EUR 2,000 per missing customer in each nonempty trip.
Maximum 50 is hard: no decoded or validated trip may exceed it. Idle vehicles
do not incur a missing-stop penalty. In the shared instance, set
`model.min_stops_penalty_eur_per_customer = 2000`. This policy replaces the
earlier assumption that both bounds must be hard for the shared benchmark.

`real_cost_eur = fuel_eur + wage_eur + maintenance_eur` is estimated operational
cost, with overtime included. `penalty_eur` is the algorithmic minimum-stop
penalty, not an operational bill. `total_eur = real_cost_eur + penalty_eur` is
the optimization score. Report real cost and penalty separately;
`true_cost_eur_ours` must refer only to `real_cost_eur`.

The soft-stop-repair source branch now implements both the soft minimum and
hard maximum. PR #8 supplies the cost separation; the former main implementation
alone did not enforce max 50 in soft mode. During integration, verify both Split
and validation enforce max 50 even when the minimum is soft, and verify cost
evaluation and selection use the same penalty-inclusive score. The current
distance-based Split is not claimed to minimize wage/overtime/penalty cost
exactly; richer cost-aware decoding remains an improvement target.

## Decisions and implementation evidence

| Decision | Reason | Limit / evidence |
|---|---|---|
| Reuse the PSO team's shared input | Avoid redundant data generation; compare identical demands, fleet and costs | Import once; maintain source IDs and checksums |
| Original lon/lat preserved | Geocoded customer locations must drive routing, rather than sampling road vertices | Nearest-vertex offsets are audited separately |
| City-wide cached OSM graph | Connect all shared addresses using one-way-aware road paths without an API key | 229,754 graph vertices; 222,862 in depot's strongly connected component; omitted turn/HGV constraints |
| Matched distance/time paths | Travel cost and wages must describe the same path | Dijkstra minimizes assumed static travel time and records its distance; not shortest-distance optimality |
| Explicit component resnap option | Two nearest vertices are disconnected from depot | Default errors; explicit opt-in records IDs 109/237 and offsets. Addresses remain unchanged |
| Permutation + customer-indexed allocation | Exposes visit order and physical-vehicle choice in a heterogeneous fleet | Fixed types are enforced; no fleet-mix search in this instance |
| Soft minimum 10 / hard maximum 50 | Match the shared PR #8 rule: penalize short trips without allowing oversized trips | Enforce max 50 in Split and validation; charge EUR 2,000 per missing stop and include it in total_eur |
| Separate monetary cost and score | Keep operational estimates distinct from search penalties | Report real_cost_eur, penalty_eur and total_eur separately; true_cost_eur_ours is money only |
| Updated soft-mode Split in Subhan's branch | Minimize missing-customer count first, distance second, while keeping max 50 hard | Lexicographic preference is not an exact minimizer of the finite penalty-inclusive monetary objective |
| OX, tournament, two elites | Preserve feasible incumbents and combine order information | No measured evidence here that OX improves mean performance |
| Directed 2-opt with cost guard | Reversal changes internal directed arcs; shorter distance can increase time/wages | One bounded pass; cost acceptance at vehicle-batch level can miss improvements |
| NN seed and unseeded ablation | Test how much apparent improvement comes from initialization | No NN benefit established in the historical hard-10–50 experiments; unseeded mean slightly lower. New shared-policy runs remain required |
| Group mutation in the earlier hard-minimum experiment | Single-customer moves cannot activate an empty vehicle when ten stops are mandatory | Historical design rationale only: under the current soft minimum such moves are feasible but penalized. Re-evaluate the neighborhood rather than claiming this barrier still applies |
| Cheapest-insertion repair for short trips | Try to dissolve underfilled trips by moving customers into other trips with capacity and stop room | All-or-nothing per short trip; insertion uses distance rather than full wage/penalty cost; no guarantee of zero penalties on other instances |
| Spatial block mutation | Select the ten nearest customers compatible with the target vehicle | Tested as part of a combined revised algorithm, not an isolated improvement claim |
| Re-evaluate the fixed PSO reference on road matrices | Avoid stale times and costs after changing distance/time inputs | Visit order and vehicle assignments unchanged; rescheduling is not another PSO search |
| Keep generated artifacts outside code PR | Keep review focused and reproducible | Cache/raw extracts, generated matrices, maps and experiment runs are ignored; distribute one checksum-identified benchmark separately |

Research connections: Prins (2009) motivates heterogeneous memetic routing;
Vidal (2022) motivates combining population search and route neighborhoods;
Zhao et al. (2024) shows why multi-trip scheduling needs a tailored Split.
This prototype implements neither full HGS nor these papers' full methods.
References and reading-status qualifications are in REFERENCES.md and
RESEARCH_AND_ALGORITHM.md. AI assistance is disclosed; code execution is not
evidence of each member's understanding.

## Historical evidence and next iterations

The recorded five-seed ablations used hard 10–50 bounds. They do not establish
performance or operator benefits for the PR #8 soft-minimum/hard-maximum rule.
Keep those runs labeled as historical and rerun after integration with the same
shared road file, explicit penalty setting and separate cost/score fields.

Next algorithm iterations: cost/time-aware splitting, a constructive capacity-
and maximum-stop-feasible load-balanced seed, spatial relocation/swap neighborhoods,
and diversity/restarts.
Evaluate each against the same frozen matrix and seeds, keeping only supported
improvements. Horizon/rest modeling depends on the agreed problem definition.


## Current measured revision and responsibilities

Subhan implemented the soft-stop repair mechanisms and ran the pilot at commit
`48f3367693ea36c53a0964fad47f90f9ec3af1f4`: five cost-GA seeds,200 generations, population 32 and 6,032
evaluations per run. HU revalidated the stored plans, refreshed the stale PSO
reference block, preserved the shared road matrices, and updated the documents.
Dorina's cost evaluator separates `real_cost_eur`, `penalty_eur` and `total_eur`.
This division avoids duplicate algorithm experiments and credits individual work.

Mean cost/score EUR 1,473.3936; best EUR 1,461.0733; sample SD EUR 7.4471;
zero final penalties for all five cost-GA seeds. The fixed PSO-team plan's road
re-evaluation is EUR 1,472.0597 with 28.4723overtime hours. The EUR 10.99 difference
is to that fixed plan, not proof of superiority to a newly optimized PSO method.

The best new GA plan uses all five vehicles but still has an 18.69-hour maximum
work span, so daily/rest realism remains unresolved. Changes in budget, minimum
policy, Split and repair are confounded relative to the earlier hard study;
do not claim isolated causal benefits. New source code needs its own review.
