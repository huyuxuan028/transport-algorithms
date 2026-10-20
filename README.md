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

Optional figures:

```powershell
python -m pip install matplotlib
python plot_results.py
```

## Problem variant

Heterogeneous fleet, one physical VW Caddy, Sprinter and MAN, with repeated
sequential depot tours. Each customer order is indivisible and served once.
Each trip has both a weight and aggregate-volume limit of its assigned vehicle.
All customers are available at time zero. There is no daily time horizon.
One of each type is an explicit initial fleet assumption, not established by
the instructor listing three possible vehicle types.

The default objective is **estimated fuel litres**, proposed because the brief
supplies different fuel-consumption rates. It is a constant-rate distance proxy,
not a physical fuel model. Pure total distance is also implemented. Agree the
final objective and time-horizon rules with the supervisor before a competition.
With unrestricted reuse and distance alone, the largest vehicle can simulate
smaller vehicles' routes, so smaller vehicles have no distance advantage.

## Representation and operators

A genotype contains two arrays: (1) a permutation of customer IDs; (2) vehicle
assignment indexed by customer ID, not by current permutation position. Filtering
the permutation by each vehicle gives that vehicle's visit order. A dynamic
programming Split procedure inserts capacity-feasible trip boundaries. Repeated
trips are scheduled sequentially for the same physical vehicle.

Order crossover operates on the permutation. Uniform inheritance operates on
the customer-indexed assignments. Assignment mutation chooses only a vehicle
that can carry that complete customer order. Permutation mutation swaps or
reverses visits. Tournament size is three, crossover probability is 0.9, order
and assignment mutation probabilities are 0.3, and two elite candidates survive.
Bounded within-trip 2-opt improves routes. Population and generation counts are
CLI parameters. This is an educational GA, not a reproduction of published HGS.

Split is exact for boundaries of a fixed order/allocation under the implemented
additive capacities and unlimited horizon. It is not globally exact over all
permutations and allocations. With fixed per-vehicle fuel rate, minimizing each
vehicle's trip distance also minimizes its estimated fuel. Changing time-window,
release-time, refuelling or shift-limit assumptions requires a different decoder.

## Evidence

Six algorithm tests cover independent exhaustive Split comparison, correct
customer-indexed allocation, coverage and overload rejection, multi-trip overlap,
parcel aggregation and elitism. Four complementary generator tests are in the
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
Our explicit two-array allocation is a simpler design choice, not a claim that
those papers implement exactly this chromosome or this prototype.
