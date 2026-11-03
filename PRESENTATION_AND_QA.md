# Algorithm presentation and questions

## Suggested demonstration order
1. Show the chromosome example in RESEARCH_AND_ALGORITHM.md; explain customer-ID indexing of assignments.
2. Open ox, split_vehicle, repair and solve in solver.py. Explain one operation, not just its name.
3. Show research_results/convergence.png and SUMMARY.md. Explain experimental controls and limitations.
4. Explain which literature concepts informed the audit and which are still reading tasks.
5. Explain the road-network adapter honestly: software and offline tests exist, but live data needs agreed coordinates and an ORS key.

## Short oral presentation
Our project uses a genetic algorithm with local search for a fixed heterogeneous fleet and repeated depot-return trips. Each chromosome contains a customer permutation and an assignment to physical vehicles. The five vehicle types remain fixed. We repair assignments when an individual order does not fit its assigned vehicle.

For each vehicle sequence, dynamic programming selects capacity-feasible trip boundaries by distance. A bounded 2-opt search then improves each trip. The outer GA evaluates fuel, maintenance and wages, including overtime across all trips. We recognize that this distance-based decoder is not an exact cost optimizer.

The population retains two elites. Tournament selection chooses parents, order crossover combines customer permutations, and uniform inheritance combines assignments. Swap, reversal and reassignment mutations explore alternatives.

We audited this structure against work by Prins on Split-based evolutionary routing and heterogeneous-fleet memetic algorithms, and Vidal on hybrid genetic search. Our implementation is a simpler adaptation, not a reproduction or a novel HGS contribution. We compare it with random search and operator ablations over multiple seeds. Remaining work includes jointly agreed road data, cost-aware local search, diversity control and operational constraints.

## Questions everyone must answer independently
- Why encode assignment separately? It makes physical-vehicle capacity compatibility explicit. Trade-off: larger search space and repair bias; joint heterogeneous Split is an alternative in the literature.
- Is Split globally optimal? No. It finds minimum distance contiguous partitions for a fixed per-vehicle order before local search; it does not find the global VRP optimum or wage-aware optimum.
- What does crossover preserve? OX preserves a parent subsequence and the other parent's relative ordering. It does not guarantee good routes or assignment compatibility; repair and evaluation remain necessary.
- Why local search? Evolution explores combinations; 2-opt improves local route order. The ablation tests its empirical contribution. Distance-based moves may not reduce road-time-based wages.
- Why does the curve converge? Elites guarantee a non-worsening incumbent, but stagnation may be premature. No optimality inference follows.
- What is unique? Separate assignment and per-vehicle repeated-trip decoding is our implementation choice for this simplified problem. Novelty has not been established.
- Which constraints are missing? Hard min/max stop counts, 3D packing, rest/multi-day rules, time windows and vehicle-specific road restrictions.
- What is the road-data status? Directed matrix support and real-geometry map code are tested offline. Live ORS requests have not been run; current numerical results remain Euclidean.
