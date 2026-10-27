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

## Problem variant

Five physical vehicles, each chosen by the GA from VW Caddy, Sprinter and MAN, with repeated
sequential depot tours. Each customer order is indivisible and served once.
Each trip has both a weight and aggregate-volume limit of its assigned vehicle.
All customers are available at time zero. There is no daily time horizon.
The generator's two-Caddy, two-Sprinter, one-MAN mix is only a feasible witness,
not a constraint on the optimized fleet.

The default objective is **estimated fuel litres**, proposed because the brief
supplies different fuel-consumption rates. It is a constant-rate distance proxy,
not a physical fuel model. Pure total distance is also implemented. Agree the
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

Eight algorithm tests cover independent exhaustive Split comparison, correct
customer-indexed allocation, coverage and overload rejection, multi-trip overlap,
parcel aggregation, type-dependent capacity/fuel and elitism. Four complementary generator tests are in the
generator repository. The pilot has 12 runs: two objectives, two search methods,
three seeds, population 32 and 80 generations. Both methods use 2,432 candidate
evaluations and the same decoder/2-opt; runtimes are not budget-matched. This is
development evidence, not a held-out comparison with the swarm team. Exact gaps
are unavailable because there is no certified optimum for this new instance.

The generator's proxy-data warning is inherited. No 3D packing, time windows,
road network or driver-shift feasibility is established. Long schedules are
allowed under the initial unrestricted-horizon simplification.

## Research basis

See the separate findings repository for complete references. Relevant works
include Prins (2009) on memetic heterogeneous-fleet routing, Vidal (2022) on HGS,
Zhao et al. (2024) on multi-trip splitting, and Hvattum (2025) on split starts.
Our explicit three-array representation is a simpler design choice, not a claim that
those papers implement exactly this chromosome or this prototype.


## Cost and Evaluation Engine Calibration Notes

Driver wages and fuel price defaults are calibrated from official EU statistical benchmarks as baseline assumptions until supervisor values are provided:
- Driver wage: €20.00/h base (Eurostat dataset `lc_lci_lev`, NACE Rev. 2 Section H Division 49 Land Transport average labour cost), with double wage (€40.00/h) for shift duration exceeding 8 hours per project brief.
- Fuel price: €1.65/L diesel (European Commission DG ENER Weekly Oil Bulletin EU weighted pump average).
- Maintenance: €50 (Caddy), €80 (Sprinter), €120 (MAN) per 1,000 km based on commercial fleet servicing and wear benchmarks.
- Volume buffer: Configurable (default 0.10) to support Course Option 1 reserve loading.
