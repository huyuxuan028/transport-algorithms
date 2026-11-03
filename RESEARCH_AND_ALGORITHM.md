# Algorithm background and reading status

The active benchmark is `data/shared_pso_250.json`; road experiments use
`data/shared_pso_250_road.json`. The old Keleti map is not a final benchmark.
The source fleet is two Caddy, two Sprinter and one MAN. See DESIGN_DECISIONS.md
and RESULTS_AND_LIMITATIONS.md for the current implementation and measured results.
These notes explain the implementation and distinguish source review from reproduction.

# Algorithm research and implementation audit

## Honest status
This is a simplified educational GA with local search, not a reproduction of HGS or a novel published algorithm. The papers below were reviewed after the initial implementation to audit and improve the design. Do not claim the initial code was derived from them. Each teammate must read the papers and trace the code before presenting these decisions as understood.

## Problem and constraints
Fixed heterogeneous fleet, five physical vehicles (2 Caddy, 2 Sprinter, 1 MAN); multiple sequential depot-return trips; indivisible delivery orders; each customer served exactly once. Weight and buffered volume are hard constraints. Vehicle allocation must fit each individual order. Drivers accumulate work across trips. Fuel, maintenance per 1,000 km, and regular/overtime wages form the cost. Eight hours is the regular-pay threshold, not a hard work limit. The current model permits arbitrarily long days: realistic rest periods and multi-day scheduling remain absent. Minimum 10 / maximum 50 stops default to soft audits; stop_count_mode=hard enforces them in both Split and validation. No geometric packing, time windows, or load-dependent fuel. Truck-specific access constraints are not modeled by the common simplified motorcar graph.

## Representation and decoding
A chromosome is (permutation, assignment indexed by customer ID, vehicle types). On the fixed benchmark, vehicle types are constant and not searched. Example permutation [3,1,4,2], assignment [1,1,0,0] gives vehicle 0 sequence [3,4] and vehicle 1 sequence [1,2]. Indices are zero-based. Repair changes incompatible assignments to eligible physical vehicle slots.

For each vehicle sequence, dynamic programming chooses contiguous trip boundaries. With D[0]=0, D[j] is the minimum of D[i] + distance(depot, sequence[i:j], depot), over feasible segments. The segment must respect weight and buffered volume and, in hard mode, stop bounds. Complexity is O(n_v²), and the sum across vehicles is at most O(n²). This is exact ONLY for the fixed sequence's distance-based partition, before local search. It does not jointly optimize assignment, order, or wage-aware cost. ORS routes are directed; matrices must not be averaged to force symmetry.

One best-improvement distance-based 2-opt reversal per trip is applied during decoding. With independent road travel times, a shorter-distance reversal may increase wage cost; the cost-objective path rejects a whole vehicle's distance-improved batch if it increases its financial cost. This guard is not a full cost-aware neighborhood. Directed reversal cost includes internal reversed arcs. Trip service time is added to road travel seconds / 60, if available; otherwise an explicitly labeled constant-speed approximation is used. Decoder-improved order is inherited (a Lamarckian update), but fitness and genome are not identical objects: regrouping the global permutation can alter future crossover behavior.

## Evolution, as implemented in solver.py
1. Start with the neutral imported reference plan, a nearest-neighbor order using the same assignment, and remaining random repaired candidates. The unseeded ablation omits nearest-neighbor seeding. This witness dependency limits input interchange: shared data must provide a feasible reference plan or an adapter must construct one.
2. Minimize financial cost (other objective modes remain available).
3. Keep two elites. Each parent is selected by a tournament of three.
4. Order crossover (OX), probability 0.9: retain a segment from one parent and fill remaining positions in the other parent's cyclic order. Assignment uses independent uniform inheritance.
5. With probability 0.3, mutate order by swap or reversal; separately with probability 0.3, mutate one assignment to an eligible physical slot (or a minimum-size group in hard-stop mode). Repair, decode, score.
6. Repeat for the requested generations. Best-so-far values cannot increase because of elitism. A flat curve can indicate stagnation, NOT global optimality.

For population P and G generations: P + G(P-2) decoder evaluations normally; hard-mode fallback seeding adds counted evaluations when necessary. A decoder is approximately O(n²) plus route local search; total upper-order bound O(PG n²), excluding API preprocessing. Matrices use O(n²) memory. Diversity counts are recorded, but no active diversity management or restarts are currently implemented; duplicate decoded plans and premature convergence are plausible weaknesses.

## Literature-to-code map

| Source | What it contributes | Relation to this project |
|---|---|---|
| Prins (2004), A simple and effective evolutionary algorithm for the vehicle routing problem. DOI: https://doi.org/10.1016/S0305-0548(03)00158-8 | Permutation without trip delimiters, Split and local-search hybridization | Conceptual foundation for auditing our decoder; our separate allocation chromosome, heterogeneous vehicles and multi-trip wages differ. Not a reproduction. |
| Prins (2009), Two memetic algorithms for heterogeneous fleet vehicle routing problems. DOI: https://doi.org/10.1016/j.engappai.2008.10.006 | Directly relevant heterogeneous-fleet giant-tour decoding, vehicle allocation, local search and diversification | We explicitly assign customers to physical vehicles before per-vehicle Split, unlike the paper's joint trip and vehicle allocation procedure. Published abstract and accessible section previews reviewed; full paper still needs team reading. |
| Vidal, Crainic, Gendreau and Prins (2014), A unified solution framework for multi-attribute vehicle routing problems. DOI: https://doi.org/10.1016/j.ejor.2013.09.045 | Separates assignment, sequencing and route evaluation concerns | Architectural reading for adapting constraints; our small solver is not UHGS. Publisher abstract reviewed, not a full reproduction. |
| Vidal (2022), Hybrid genetic search for the CVRP: Open-source implementation and SWAP* neighborhood. DOI: https://doi.org/10.1016/j.cor.2021.105643 ; author code https://github.com/vidalt/HGS-CVRP | Reference HGS implementation and advanced local search | A comparison target on compatible standard CVRP instances. We do not implement SWAP*, HGS diversity control, or its full feasibility management. |
| Hvattum (2025), Where to Split in Hybrid Genetic Search for the Capacitated Vehicle Routing Problem. DOI: https://doi.org/10.3390/a18030165 | Examines the effect of the giant-tour starting point on Split | Candidate future experiment: vary sequence starting points; not implemented or validated here. Author record: https://www.himolde.no/english/employees/log/aca/hvattum/ |

These CVRP papers do not establish correctness or performance for our heterogeneous multi-trip cost extension. Full reading of the heterogeneous-fleet work and a targeted review on multi-trip wage-aware routing remain necessary before a complete academic report. No state-of-the-art performance claim is made.

## Experiments and decision criteria
research_experiments.py compares full GA, matched-evaluation random search, GA without local search, and GA without order crossover, plus an unseeded-GA ablation in the revised experiments. Five seeds share population, generation budget, initial witness, objective and input. Report all runs, mean, sample SD, runtime, feasibility and best-so-far curves. Both full GA and random search use the same local-search decoder; random search is not pure random routing. Disabling order crossover still retains assignment recombination. Equal evaluation counts are not equal wall-clock budgets. Five seeds support exploratory evidence, not a robust significance claim.

The current measured study uses the shared Budapest road extension, five seeds per variant and hard stop bounds. Repeat on multiple instance sizes after joint acceptance of the road-file hash and model. A fair PSO comparison requires identical instance hash, fleet, constraints, objective evaluator and stopping budget. For HGS or OR-Tools on standard CVRP, report a separate compatible experiment; do not compare their homogeneous single-trip objective directly with this cost model. No gap without a valid same-problem reference bound or optimum.

## What each teammate must be able to demonstrate
Trace the four-customer example through assignment, one Split recurrence, OX, mutation, repair and cost. Explain exactly why two elites preserve incumbent quality, why local-search ablation is informative, and why cost Split, rest constraints, diversity and truck restrictions remain limitations. Do not replace this understanding with reading a prepared script.
