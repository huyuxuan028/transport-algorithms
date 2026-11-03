# Measured results and limitations

## Soft-stop scenario: five seeds per variant
Same actual Budapest OSM graph, existing 250 orders, fixed five-vehicle inventory, scenario cost coefficients, population 32, 80 generations and 2432 evaluations per run. Distances are along directed graph paths; times use estimated road-class speeds. Stop counts are audited, not enforced, in THIS table. Both seeded random search and seeded GA receive the nearest-neighbor candidate. See runs.json for all seeds and runtime.

| Variant | Mean cost EUR | Sample SD | Best | Worst |
|---|---:|---:|---:|---:|
| random_search | 625.66 | 0.00 | 625.66 | 625.66 |
| ga | 620.29 | 1.12 | 618.34 | 621.03 |
| ga_unseeded | 660.08 | 3.93 | 656.11 | 666.53 |
| ga_no_local_search | 625.88 | 0.40 | 625.39 | 626.41 |
| ga_no_order_crossover | 619.62 | 1.36 | 618.52 | 621.48 |

One-pass nearest-neighbor baseline (reference vehicle assignments, same decoder/local search): 625.66 EUR. This is a separate one-construction reference, not a budget-matched competitor.

Interpretation: nearest-neighbor seeding accounts for much of the improvement over the original unseeded GA. The complete seeded GA achieves a small additional improvement over its seed. Removing OX does not hurt the measured mean; in this small experiment its mean is slightly better. This is not evidence that OX is beneficial or globally unnecessary. No p-values, optimality gap, state-of-the-art claim or general convergence guarantee is asserted. Identical seeded random results mean it retained the initial seed, not that random search is universally deterministic.

The GA mean and SD describe this ONE small geographic scenario. They do not establish robustness across cities, order sets or operating constraints. Evolutionary behavior still needs study on multiple held-out instances. Unique decoded-plan counts in each history can expose diversity loss even when a best-so-far curve is flat.

## Hard 10–50 stop scenario: distinct model
Five additional seeds enforce both bounds in Split and the independent validator. All five recorded plans have zero below/above-bound trips. Mean cost is 870.09 EUR; sample SD is 22.45. Extra initialization evaluations are recorded (typically 2433). Do NOT compare this cost to the soft table as an algorithm improvement: the feasible sets differ.

Hard-policy plans can contain very long single-driver work spans. Eight hours is currently a wage threshold, not a maximum shift. These plans are not claimed to be realistic working-day schedules. Further scheduling and balancing may be needed depending on the agreed course constraints.

## Actual changes versus still pending
Implemented: directed graph matrices, source-linked actual geometry, per-vehicle speed fallback, road-duration scheduling, fixed-fleet checks, hard-stop option, group reassignment, cost acceptance guard, nearest-neighbor seeding and reproducible ablations.

Pending: PSO data/evaluator agreement, PR conflict resolution and review, live ORS if required, model agreement for geometric packing/rest/truck restrictions, broader experiments, and each member's demonstrated understanding. A file package cannot complete real collaboration or guarantee a grade.

## Reproduction pointers
- Source hash and input hash: experiment runs JSON and package MANIFEST.json.
- Original unseeded road pilot: budapest_experiments/; reproduce with heuristic_seed=False for all variants. Earlier experiment scripts lacked the extra unseeded-GA row; retain the explicit archive distinction.
- Current revised study: research_experiments.py --instance data/budapest_road.json.
- Hard scenario: hard_policy_experiments.py.
- Static real-road map: plot_road_map.py. Online street map / offline graph map: map_budapest.py.
