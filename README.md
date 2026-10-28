# Heterogeneous Multi-Trip Genetic Algorithm

Initial implementation for a simplified furniture routing problem. Python 3.10+
and standard library only for solving, validation and repeated experiments.

## Run

```powershell
python solver.py
python solver.py --objective distance --output results/distance_solution.json
python -m unittest -v test_solver
python run_experiments.py
```

`data/example.json` is a frozen copy of the generator's development case. Keep
its checksum with experiments. No relative sibling-repository import is needed.
It is retained as a schema-v2 baseline. The shared schema-v3 development and
fixed-fleet benchmark copies are `data/development.json` and
`data/benchmark_250.json` from `transport-generator` (seed 42). The latter has
exactly five given physical vehicles: one Caddy, two Sprinters, two MAN trucks.
The generated-witness routes are used for a feasible initial candidate, never
as a purported optimum. Output contains all transports, physical vehicle IDs,
trip schedules, chromosome, distance, fuel estimate, settings and validation.

Optional figures and benchmark table:

```powershell
python -m pip install matplotlib
python plot_results.py
python plot_results.py --results results/solution.json --pilot results/pilot.json --instance data/example.json --out figures --shift-hours 8
python -m unittest -v test_plot_results
```

`plot_results.py` writes to `figures/`: `dataset.png` (customer map and order
weight/volume/service-time histograms), `routes.png` (generated witness plan
next to the GA plan, one colour per physical vehicle), `gantt.png` (trips per
vehicle on a time axis with the shift line, so overtime is visible),
`utilisation.png` (payload/volume use and stops per trip against the 10-50
brief), `convergence.png` (GA vs random per objective) and `BENCHMARK.md`
(per-run table from `results/pilot.json`). The shift length and volume buffer
default to `model.shift_hours` / `model.volume_buffer` in the instance when
present; the optional `cost` block of a solution is shown when present.

To run the shared schema-v3 development case and regenerate comparable figures:

```powershell
python -m unittest -v test_solver test_plot_results
python run_experiments.py --instance data/development.json --pilot-output results/pilot_v3.json --solution-output results/solution_v3.json --best-objective cost
python plot_results.py --instance data/development.json --pilot results/pilot_v3.json --results results/solution_v3.json --out figures/schema_v3
```

The generated `results/pilot_v3.json` records three seeds, 32 individuals and
80 generations for each method and objective. `figures/schema_v3/BENCHMARK.md`
has the matched-evaluation GA versus random baseline. Runtimes are not matched.
For a fixed-fleet 250-customer demonstration, use:

```powershell
python solver.py --instance data/benchmark_250.json --objective cost --population 32 --generations 80 --output results/benchmark_250_cost.json
python plot_results.py --instance data/benchmark_250.json --results results/benchmark_250_cost.json --pilot results/no_pilot_for_250.json --out figures/benchmark_250
```

The latter produces dataset, route, Gantt and utilisation figures, but no
convergence comparison or multi-seed benchmark until a separate 250-customer
pilot is run. `results/benchmark_250_cost.json` is one GA seed, not a certified
optimum or a gap measurement.

## Problem variant

Five physical vehicles, chosen by the GA from VW Caddy, Sprinter and MAN when
`model.fleet_mix_is_decision=true`, with repeated
sequential depot tours. Each customer order is indivisible and served once.
Each trip has both a weight and aggregate-volume limit of its assigned vehicle.
All customers are available at time zero. There is no daily time horizon.
The generator's two-Caddy, two-Sprinter, one-MAN development mix is only a
feasible witness. With `fleet_mix_is_decision=false`, as in the 250-customer
case, the given five vehicles are fixed: crossover, mutation, repair and
validation preserve their types and physical identities. The solver uses
`vehicles[].speed_kmh` when present, falling back to the legacy model speed.

The default objective is **estimated fuel litres**, proposed because the brief
supplies different fuel-consumption rates. It is a constant-rate distance proxy,
not a physical fuel model. Pure total distance and financial cost (fuel,
driver wage including overtime, maintenance) are also implemented. Agree the
final objective and time-horizon rules with the supervisor before a competition.
With unrestricted reuse and distance alone, the largest vehicle can simulate
smaller vehicles' routes, so smaller vehicles have no distance advantage.
Five vehicles are available; idle slots are permitted. With no shift horizon or
fixed fleet cost, the mix need not be unique or operationally optimal. The GA
reports the best solution found under a limited search budget.

## Representation and operators

A genotype contains three arrays: (1) a permutation of customer IDs; (2) physical
vehicle assignment indexed by customer ID; (3) five vehicle-type choices. Filtering
the permutation by each vehicle gives that vehicle's visit order. A dynamic
programming Split procedure inserts capacity-feasible trip boundaries. Repeated
trips are scheduled sequentially for the same physical vehicle.

Order crossover operates on the permutation. Uniform inheritance operates on
the customer-indexed assignments and vehicle types. Mutation changes order,
assignment or type; incompatible assignments are repaired to a vehicle that can
carry the whole order. Permutation mutation swaps or reverses visits. Tournament
size is three, crossover probability is 0.9, and each of the three mutation
probabilities is 0.3. Two elite candidates survive.
Bounded within-trip 2-opt improves routes. Population and generation counts are
CLI parameters. This is an educational GA, not a reproduction of published HGS.

Split is exact for boundaries of a fixed order/allocation under the implemented
additive capacities and unlimited horizon. It is not globally exact over all
permutations and allocations. With fixed per-vehicle fuel rate, minimizing each
vehicle's trip distance also minimizes its estimated fuel. Changing time-window,
release-time, refuelling or shift-limit assumptions requires a different decoder.

## Evidence

Seventeen algorithm tests cover independent exhaustive Split comparison, correct
customer-indexed allocation, coverage and overload rejection, multi-trip overlap,
parcel aggregation, type-dependent capacity/fuel, financial cost, fixed fleet,
per-vehicle speed and elitism. The generator repository has six complementary
tests. The schema-v3 pilot has 18 runs: three objectives, two search methods,
three seeds, population 32 and 80 generations. Both methods use 2,432 candidate
evaluations and the same decoder/2-opt; runtimes are not budget-matched. This is
development evidence, not a held-out comparison with the swarm team. Exact gaps
are unavailable because there is no certified optimum for this new instance.

The generator's proxy-data warning is inherited. No 3D packing, time windows
or road network is established. Long schedules are allowed; overtime beyond
eight hours is priced rather than treated as infeasible. The 10–50 stops per
trip range is audited, not enforced as a hard constraint.

## Research basis

See the separate findings repository for complete references. Relevant works
include Prins (2009) on memetic heterogeneous-fleet routing, Vidal (2022) on HGS,
Zhao et al. (2024) on multi-trip splitting, and Hvattum (2025) on split starts.
Our explicit three-array representation is a simpler design choice, not a claim that
those papers implement exactly this chromosome or this prototype.


## Cost and Evaluation Engine Calibration Notes

Cost inputs are assumptions pending supervisor-approved values:
- Driver wage: €20.00/h is a generic fallback, not a measured driver wage; per-vehicle wage values in an instance take precedence. Overtime is paid at double rate after 8 hours per the project brief.
- Fuel price: €1.65/L diesel (European Commission DG ENER Weekly Oil Bulletin EU weighted pump average).
- Maintenance: €50 (Caddy), €80 (Sprinter), €120 (MAN) per 1,000 km based on commercial fleet servicing and wear benchmarks; instance values take precedence.
- Volume buffer: configurable (default 0.10) to support Course Option 1 reserve loading.

