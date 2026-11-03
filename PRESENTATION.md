# Short presentation

We now use the other team's shared dataset: 250 Budapest customer addresses and
five fixed vehicles. We preserve their orders, capacities and cost parameters.
We replaced approximate straight-line distances with directed paths on a cached
OpenStreetMap road graph covering all shared locations. Distance and travel time
are measured along the same path, and address-to-road offsets are recorded.

Our chromosome stores customer order and physical vehicle allocation. A dynamic
program splits each vehicle's sequence into capacity-feasible depot trips.
The selected experiment also enforces ten to fifty customers per trip. Tournament
selection, order crossover, mutation and bounded directed 2-opt improve candidates.
Fitness includes fuel, maintenance and wages, with double pay beyond eight hours.

We ran five seeds for five algorithm variants. The main GA's mean cost was about
1,944 euros, compared with 2,102 for seeded random search. All runs passed the
implemented constraints. Removing local search worsened performance; the NN and
crossover ablations do not establish a benefit from those mechanisms on this case.

Important limitations remain. The graph omits turn restrictions and truck clearance,
and the solver permits very long work spans. The best main-GA plan has a vehicle
working about fifty-one hours, so we do not present it as a realistic single-day
schedule. Our next steps are to agree the planning horizon, improve allocation
and cost-aware splitting, and compare both teams on the identical road matrices.

Show: shared input and provenance; chromosome/decode code; convergence and ablations;
constraint audit; new street-map route overlay. Explain one customer allocation and
one split decision from memory. Do not present the old PSO cost as a road benchmark.
