# Current progress presentation

We now share the PSO team's 250 Budapest customer records, five fixed vehicles,
and operating parameters. My work focused on the OSM road integration, interactive
route map, reference-plan audit and documentation. Dorina implemented the cost
separation, and Subhan developed the soft-stop repair and ran the new experiments.

Our chromosome represents customer order and physical-vehicle allocation. Split
creates capacity-feasible depot trips. The revised soft-mode decoder prioritizes
fewer missing customers, then distance, and enforces a hard maximum of fifty.
Short trips are repaired by cheapest insertion, and spatial group mutation
moves nearby compatible customers. This is a simplified educational GA, not HGS.

The agreed rule allows trips below ten customers with a two-thousand-euro penalty
per missing customer. Real operating cost is reported separately from the total
optimization score. Subhan ran five cost-GA seeds with 32 individuals and 200
generations, using 6,032 candidate evaluations per run. I checked the stored plans:
mean real cost is approximately 1,473.39euros, best 1,461.07, with zero penalties.

I also corrected the embedded PSO-team reference plan by rescheduling the same
routes on the road matrices. Its real cost is 1,472.06euros and overtime 28.47
vehicle-hours. This is a fixed reference-plan re-evaluation, not a new PSO run.
The revised JSON changes only this audit block; the road matrices remain identical.

The best new GA plan uses all five vehicles, but its longest work span is still
about 18.69hours. Road times are estimates and truck/turn restrictions are incomplete.
Our next steps are broader comparisons, cost-aware decoding and realistic horizon
modeling. The old 80-generation hard-stop results are historical, not the new study.

Show: current result artifact and per-seed table; Split and repair implementation;
convergence; road-route visualization; shared rules and individual contributions.
The old three-vehicle map remains an old-result map until regenerated from the new
solution. Do not display its EUR 1,926.69/51-hour figures as current results.
