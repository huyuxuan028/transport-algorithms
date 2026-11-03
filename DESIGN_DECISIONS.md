# Intentional design and evidence

| Decision | Reason | Limit / evidence |
|---|---|---|
| Reuse the PSO team's shared input | Avoid redundant data generation; compare identical demands, fleet and costs | Import once; maintain source IDs and checksums |
| Original lon/lat preserved | Geocoded customer locations must drive routing, rather than sampling road vertices | Nearest-vertex offsets are audited separately |
| City-wide cached OSM graph | Connect all shared addresses using one-way-aware road paths without an API key | 229,754 graph vertices; 222,862 in depot's strongly connected component; omitted turn/HGV constraints |
| Matched distance/time paths | Travel cost and wages must describe the same path | Dijkstra minimizes assumed static travel time and records its distance; not shortest-distance optimality |
| Explicit component resnap option | Two nearest vertices are disconnected from depot | Default errors; explicit opt-in records IDs 109/237 and offsets. Addresses remain unchanged |
| Permutation + customer-indexed allocation | Exposes visit order and physical-vehicle choice in a heterogeneous fleet | Fixed types are enforced; no fleet-mix search in this instance |
| Contiguous DP Split | Avoid trip separators in chromosome; obtain best distance partition for a fixed order/allocation | Not a wage/overtime-optimal decoder or global routing optimum |
| OX, tournament, two elites | Preserve feasible incumbents and combine order information | No measured evidence here that OX improves mean performance |
| Directed 2-opt with cost guard | Reversal changes internal directed arcs; shorter distance can increase time/wages | One bounded pass; cost acceptance at vehicle-batch level can miss improvements |
| NN seed and unseeded ablation | Test how much apparent improvement comes from initialization | No NN benefit established on the new hard-stop instance; unseeded mean slightly lower |
| Hard-stop group mutation | Single-customer moves cannot populate an empty vehicle requiring ten stops | Random groups have weak spatial/load structure; long work spans expose poor balancing |
| Keep generated artifacts outside code PR | Keep review focused and reproducible | Cache/raw extracts, generated matrices, maps and experiment runs are ignored; distribute one checksum-identified benchmark separately |

Research connections: Prins (2009) motivates heterogeneous memetic routing;
Vidal (2022) motivates combining population search and route neighborhoods;
Zhao et al. (2024) shows why multi-trip scheduling needs a tailored Split.
This prototype implements neither full HGS nor these papers' full methods.
References and reading-status qualifications are in REFERENCES.md and
RESEARCH_AND_ALGORITHM.md. AI assistance is disclosed; code execution is not
evidence of each member's understanding.

Next algorithm iterations: cost/time-aware splitting, a constructive hard-feasible
load-balanced seed, spatial relocation/swap neighborhoods, and diversity/restarts.
Evaluate each against the same frozen matrix and seeds, keeping only supported
improvements. Horizon/rest modeling depends on the agreed problem definition.
