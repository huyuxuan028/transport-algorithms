# Budapest 250 workday evaluator and initialization audit

This audit uses the 250 Budapest customer addresses, the fixed five-vehicle
fleet and the directed road matrices in
`data/shared_pso_250_road.json` (SHA-256
`6d794dff4a03cebb1f9127796209fa1f263450a780ce76ade9c26244b6a2676c`).
Both searches use the cost objective, a 960-minute workday, random seed 0,
population 32, 200 generations and exactly 6,032 candidate evaluations each.
The experiment covers one run per arm on this instance.

## Evaluator cross-check

The controlled fixture starts with a validated 70-customer plan containing
a 50-stop trip and a 20-stop trip. Each test copies the fixture and reschedules
the changed trips so stored travel, fuel and work times agree with the inputs.
Weight and volume are changed independently. Trip splits and moves preserve
coverage except in the two coverage tests.

| Check | Expected | Actual from `validate_solution` |
|---|---|---|
| Original plan | Feasible, €0 penalty | Feasible, €0 |
| 101 kg against 100 kg payload | Hard rejection | `Overloaded trip` |
| 91 m³ against 90 m³ usable volume | Hard rejection | `Overloaded trip` |
| Split 50 stops into 42 and 8 | Feasible, €4,000 for the 8-stop trip | Feasible, €4,000 |
| Move one stop into the 50-stop trip | Hard rejection at 51 stops | `Hard stop-count violation` |
| Remove one stop | Hard rejection | `Missing or duplicated customers` |
| Add a second visit while retaining all originals | Hard rejection | `Missing or duplicated customers` |
| Two trips work 910 + 51 minutes on one vehicle | Hard rejection at 961 minutes | `Vehicle exceeds time_horizon_minutes` |

The existing two-trip 960/961-minute boundary test also passed. Both decoder
and validator accept minute 960 and reject minute 961. Wages at the boundary
cover eight regular and eight double-rate hours. The test suite had 41 passes
and two skips for missing Matplotlib. The raw expected and actual results are
in [evaluator_cases.json](results/workday_16h_seed_comparison/evaluator_cases.json).

## Matched-budget initialization comparison

The seeded arm starts with a decoded neutral witness, its per-vehicle
nearest-neighbor variant and 30 random chromosomes. A workday repair of the
original neutral witness contributes one additional evaluation and replaces a
population member. Generation 0 therefore costs 33 evaluations. The final
generation evaluates 29 offspring and retains one extra existing population
member to stay within budget. The unseeded arm has 32 random chromosomes and
evaluates 30 offspring in every generation. The first 30 random chromosomes
have identical stage diagnostics across arms.

In the previous implementation, `heuristic_seed=False` disabled only the
nearest-neighbor candidate. It left the witness and both initialization
fallbacks enabled. In this audit, `heuristic_seed=False` (CLI equivalent
`--no-heuristic-seed`) excludes the witness, nearest-neighbor candidate,
all-on-one-vehicle fallback and workday rebalancing seed. Both arms still use
the ordinary assignment compatibility repair, Split, intra-trip 2-opt and
short-trip repair in each candidate evaluation.

| Arm | Generation | Evaluations | Feasible population | Operating cost (€) | Soft penalty (€) | Total (€) | Longest vehicle (min) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Seeded | 0 | 33 | 1/32 (3.125%) | 1,860.5025 | 250,000 | 251,860.5025 | 958.78 |
| Seeded | 200 | 6,032 | 1/32 (3.125%) | 1,860.5025 | 250,000 | 251,860.5025 | 958.78 |
| Unseeded | 0 | 32 | 0/32 (0%) | 3,066.6536 † | 172,000 † | 175,066.6536 † | 1,712.65 † |
| Unseeded | 200 | 6,032 | 0/32 (0%) | 1,856.9747 † | 0 † | 1,856.9747 † | 1,285.79 † |

† These are diagnostic costs of the best decoded **infeasible** candidate.
Selection ranks total minutes above the vehicle horizons first, then cost.
The unseeded arm lowered its best excess from 1,761.00 to 410.48 minutes
summed over late vehicles. It returned no solution and has no feasible cost
curve. The seeded arm retained the generation-0 solution throughout, with
19 short trips and a 125-stop total shortfall. Its large soft penalty remains
part of the objective.

Measured search times were **53.82 s seeded** and **40.27 s unseeded** on
Windows 10 with Python 3.11.9. These wall-clock measurements include
initialization, candidate search and generation diagnostics. They exclude
instance validation before the search timer, final solution revalidation,
and artifact writing.

### What the random candidates looked like before and after repair

A raw chromosome supplies a customer permutation and vehicle allocations.
It has no trip boundaries, so route costs, trip feasibility and vehicle work
time become measurable only after Split. The pre-Split compatibility check
found zero incompatible customer-to-vehicle assignments in either arm,
both before and after assignment repair. Every initial random candidate
produced a partition. The table reports arithmetic means over those initial
random candidates and separates 2-opt from short-trip insertion repair.

| Arm | Stage | Horizon-feasible | Operating (€) | Penalty (€) | Total (€) | Longest vehicle (min) | Summed excess (min) |
|---|---|---:|---:|---:|---:|---:|---:|
| Seeded, random only | After Split | 0/30 | 3,703.37 | 222,000 | 225,703.37 | 1,842.00 | 2,963.67 |
| Seeded, random only | After 2-opt, before short-trip repair | 0/30 | 3,389.21 | 222,000 | 225,389.21 | 1,716.11 | 2,426.97 |
| Seeded, random only | After short-trip repair | 0/30 | 2,954.14 | 99,200 | 102,154.14 | 1,864.40 | 2,187.90 |
| Unseeded | After Split | 0/32 | 3,704.94 | 223,250 | 226,954.94 | 1,839.05 | 2,961.08 |
| Unseeded | After 2-opt, before short-trip repair | 0/32 | 3,391.05 | 223,250 | 226,641.05 | 1,714.58 | 2,425.87 |
| Unseeded | After short-trip repair | 0/32 | 2,946.35 | 94,875 | 97,821.35 | 1,878.39 | 2,178.28 |

The short-trip repair reduces penalty and total excess on average in these
samples, while increasing the mean longest-vehicle time. The stage
measurements are diagnostic snapshots and do not add optimizer evaluations.
The [convergence plot](results/workday_16h_seed_comparison/convergence.svg)
shows feasible population, feasible objective and horizon excess against
candidate evaluations. The [CSV](results/workday_16h_seed_comparison/convergence.csv)
includes every generation. Full logs are available for the
[seeded](results/workday_16h_seed_comparison/seeded.json) and
[unseeded](results/workday_16h_seed_comparison/unseeded.json) arms.

## How the GA moves customers

- The chromosome holds one global customer permutation, a vehicle assignment
  indexed by customer ID, and a type for each physical vehicle. In Budapest,
  the fleet types are fixed. Order crossover recombines permutations.
  Permutation mutation exchanges two positions or reverses a segment.
  The decoder filters the permutation by vehicle and recomputes contiguous
  trip boundaries via Split. A changed permutation can therefore put a
  customer on a different trip of the same vehicle.
- Assignment crossover selects each customer's vehicle from a parent.
  Assignment mutation sometimes reassigns one eligible customer and sometimes
  tries to reassign a nearby minimum-size block. The block heuristic checks
  the target's payload and usable volume. Compatibility repair fixes
  individually incompatible assignments before decoding. Split then enforces
  aggregate capacity and hard stop bounds at the trip level.
- Intra-trip directed 2-opt reverses a segment within one trip. In the cost
  objective, a vehicle's proposed reversals are retained only if its cost
  does not increase. The ordinary soft-stop repair tries to dissolve a
  short trip by cheapest distance insertion into other existing trips,
  including trips on other vehicles. It commits only if every customer from
  that short trip can be placed within capacity and stop limits. The full
  candidate is subsequently scored for workday feasibility.
- The separate seeded initialization repair can move individual stops off
  late vehicles to compatible trips on vehicles with remaining time. Soft
  mode can also create a singleton trip. This produces the feasible seed in
  this experiment.

The permutation exchange is a chromosome mutation. General decoded-route
pairwise `swap`, a general inter-route `relocate` neighborhood and cross-trip
tail exchange `2-opt*` are potential follow-up operators. The PSO operator
names supplied in the task refer to that team's chat discussion. The GA
currently has the targeted insertion and workday moves described above.

## Complexity against the current implementation

Let `n` be customers, `V` physical vehicles, `n_v` customers assigned to
vehicle `v`, `P` population, `G` generations, `M` maximum trip stops,
`L` soft minimum stops and `S` short trips on which repair is attempted.
For Budapest these are `n=250`, `V=5`, `P=32`, `G=200`, `M=50`, `L=10`,
with `S` varying by candidate.

**One candidate.** Filtering the permutation costs `O(Vn)` and chromosome
coverage sorting costs `O(n log n)`. Per-vehicle Split examines at most
`M` possible trip lengths at each start and costs
`O(Σ_v n_v min(n_v, M))`, with the unbounded quadratic worst case.
One directed 2-opt pass costs `O(Σ_r |r|²)`, bounded by `O(nM)) over trips.
The short-trip repair copies the routes for each attempt, tries fewer than
`L` customers per short trip and scans the current trips and insertion
positions for each. It costs `O(SL(n+V))`, including recomputation of trip
loads. Scheduling and horizon checks scan route legs and trips. The cost
evaluator groups trips by vehicle. Cost-gating the 2-opt proposals can
repeat the fleet scan for each vehicle, bounded by `O(V(n+V))` in total.
Together these terms give `C = O(n log n + V(n+V) + nM + SL(n+V))`.
Independent validation of the selected solution adds coverage and trip checks
outside the repeated candidate loop.

**Whole search.** With two elites kept, the normal evaluation count is
 `P+G(P-2)`, plus any extra counted seed/fallback evaluations. The audit
caps both arms at `B=6,032`. The candidate loop costs `O(BC)`, with an
additional `O(Bn log n)` upper bound for offspring creation for the fixed
fleet (the nearby
block mutation can sort customer subsets), and
`O((G+1)(P log P+Pn))` for population sorting and diagnostics. Road-matrix
validation is quadratic in `n` for the fixed fleet and type count.
Nearest-neighbor seed construction costs `O(Σ_v n_v²)`. The workday seed
repair has a separate `O(n³)` upper bound for fixed `V`. It can make at most
`n` moves, each scanning up to `n` source stops against up to `O(n)` destination
positions. This extra cost applies only when the seeded initialization
attempts the repair, at most twice in the current code. The directed matrices
occupy `O(n²)` memory and candidate populations occupy `O(Pn)`. The run also
retains `O(G)` generation summaries.

## Shared rules to confirm with PSO

The available chat context identifies the three PSO move names above. It does
not contain the PSO team's rule-by-rule evaluator messages. The PSO column
identifies the historical import or shared contract evidence where available,
with current evaluator behavior left open for confirmation.

| Topic | Current GA rule | PSO report or available evidence | Confirm together |
|---|---|---|---|
| Roads and addresses | Same 250 addresses and frozen directed road distance/time matrices | Historical PSO published run used approximate distances. The repository road re-evaluation concerns that fixed plan | Same file SHA-256, direction and depot indexing in a fresh PSO run |
| Fleet, depot and delivery | Fixed five vehicles, idle allowed. Each order is indivisible and visited once. Each trip returns to depot | Imported PSO dataset supplies the same five vehicles. Exact coverage and depot-return policy are listed in the shared contract | Fleet fixed in search and evaluator, exact-once coverage and every depot leg |
| Payload and volume | Hard payload and aggregate usable-volume limits. 10% volume reserve. No geometric packing | Import and shared contract describe payload and volume fields. Current reserve and geometric checks are unverified | Same usable-volume formula and packing scope |
| Stops | Minimum 10 soft, €2,000 per missing stop. Maximum 50 hard | Shared contract records the PR #8 alignment rule. Current PSO evaluator behavior is unverified | An 8-stop trip costs €4,000 in penalty and a 51-stop trip is infeasible |
| Work and wages | First departure at 08:00, accumulate road legs and loading/unloading across sequential trips, return by midnight. Eight regular hours, then double rate | PSO import records loading as work and wage assumptions. Current midnight hard bound is unverified | Test 960 and 961 minutes across two trips and compare wage breakdown |
| Objective | Operating cost = fuel + wages + maintenance. Score adds the stop penalty; hard violations are infeasible | Imported `true_cost_eur` is the PSO reported operating cost. The shared contract separates real cost from score | Compare the same three fields and use the same hard rejection rules |
| Search and budget | Strict unseeded option, counted candidate evaluations | Chat references `relocate`, `swap` and `2-opt*`. Application details and evaluation counting are unverified | Define seeds, fallback behavior, evaluation accounting and a common reporting budget |

## Reproduce

Run from the repository root in PowerShell, using a new output directory.
These commands run the controlled evaluator tests and the two Budapest 250
searches only.

```powershell
python -m unittest discover -v
python run_workday_seed_comparison.py --output generated/workday_16h_seed_comparison
python test_workday_evaluator.py | Set-Content -Encoding ascii generated/workday_16h_seed_comparison/evaluator_cases.json
```

The runner writes the two JSON logs, convergence CSV and SVG. It can also
render an existing CSV with `--plot-only` in a directory where the SVG is
absent. Saved evidence is under `results/workday_16h_seed_comparison/`.
