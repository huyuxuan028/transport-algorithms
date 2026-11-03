# Suggested presentation: five minutes, algorithm first

## 1. Problem and agreed scope
We study a fixed heterogeneous five-vehicle, multi-trip routing scenario. Orders are indivisible, each customer is visited once, and every trip must respect weight and buffered volume capacity. Cost includes fuel, maintenance and cumulative regular/overtime wages. Show the shared contract and distinguish agreed constraints from pending decisions. Do not say every operational constraint is modeled.

## 2. Mechanism
Show the four-customer permutation/allocation example, then point to the real decode, Split and OX functions. Explain the DP recurrence and that its objective is distance for a fixed sequence, not global financial optimality. Show tournament selection, elites and mutation. Explain why hard minimum stops required group reassignment instead of one-customer moves.

## 3. Research and deliberate choices
Show Prins (2009) for heterogeneous fleet splitting/assignment and Vidal (2022) for HGS as reference methods, with the exact implementation differences. Mention the multi-trip decoder literature. State which full papers each person actually read; do not turn a bibliography into a reading claim. Explain why this implementation is simpler and which weaknesses that creates.

## 4. Evidence and iteration
Show the one-pass nearest-neighbor baseline and the seeded/unseeded comparison before showing the best map. The initial GA was weaker than the simple baseline; we added it as a seed. Show convergence range bands and report five-seed variation. The no-OX variant is not worse here, so the crossover's value is still an open question. Explain possible stagnation and next experiments.

## 5. Actual Budapest map and next steps
Open Budapest_Road_Map.html. These are actual OSM street paths near Keleti with simulated delivery locations and unchanged furniture demands. The software respects basic one-way/access tags; time uses assumed speeds. It is not ORS, not HGV navigation, and not observed shipment data. The ORS adapter uses the current service endpoint and still needs a local key for live execution.

End with actual shared decisions, PRs and remaining work. Each member answers a question on someone else's component.

## Short English oral version
Our main work is now the algorithm and its design evidence. A candidate contains the customer order and allocation to physical vehicles. A dynamic programming split creates capacity-feasible trips, and the genetic search combines and modifies candidates while retaining the best solutions.

We found that the original GA was worse than a simple nearest-neighbor baseline on our Budapest scenario. We therefore added nearest-neighbor initialization and compared seeded and unseeded versions. We also changed reassignment to group moves when a hard minimum number of stops applies. These changes respond to observed weaknesses rather than being arbitrary GA components.

The map now uses actual OpenStreetMap road geometry and directed path distances near Keleti. Deliveries remain simulated. Our experiments show preliminary improvement, but not optimality or universal convergence. We still need shared-model agreement, broader comparisons, and further work on any required scheduling or truck-access constraints.
