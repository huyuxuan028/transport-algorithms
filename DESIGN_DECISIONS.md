# Design decisions and observed revisions

| Decision | Rationale | Alternative / limitation | Evidence |
|---|---|---|---|
| Explicit permutation + physical-vehicle assignment | Directly exposes order and allocation to heterogeneous capacities | Redundant search space; joint vehicle-allocation Split may be stronger | Read solver decode and Prins (2009) comparison |
| Fixed fleet when instance flag says false | Search may rearrange jobs but must not invent vehicle types | Whether inventory should be selectable is a scenario decision | Fixed-fleet rejection tests |
| DP contiguous Split | Avoids encoding trip delimiters; finds distance-minimum partition for the fixed sequence | Not global optimality or wage-optimal partition | Exhaustive small-partition test |
| Directed graph distances and durations | Real road paths include one-way streets | Local graph omits turns and truck rules | Actual OSM snapshot and directed 2-opt tests |
| Cost acceptance guard around distance 2-opt | A shorter path may take longer and increase overtime cost | Rejecting a whole vehicle's improved batch may miss beneficial subsets; not a fully cost-aware neighborhood | Cost-regression test |
| Elites + tournament selection + OX | Preserve incumbent and combine route-order information | Elitism makes the curve monotone but can mask stagnation; no proof of convergence to optimum | Multi-seed histories and unique decoded-plan count |
| Add nearest-neighbor initial candidate | The actual Budapest one-pass baseline cost was 625.66 EUR, better than the original unseeded GA's approximately 660 EUR | A strong initial seed can hide weak evolutionary operators, so retain a GA-unseeded ablation and share seed with random search | Original OSM experiments vs seeded experiments; independent baseline JSON |
| Hard-stop group reassignment | A single-customer move cannot activate an empty vehicle needing at least 10 customers | Larger moves may destroy useful structure; needs finer neighborhoods and diversity research | Initial hard-mode test stagnated with one used vehicle; group mode activates additional vehicles in the recorded runs |
| Keep hard/soft stop scenarios separate | Stop policy changes feasibility and the objective distribution | Must not cherry-pick the cheaper soft solution when hard bounds are required | Separate manifests and result directories |
| Local OSM fallback plus ORS adapter | Real roads can be demonstrated without an account key | Local routing is not ORS and is not truck navigation | Downloaded OSM API raw source; ORS integration offline tests |

## Research relationship
Prins (2004): permutation+Split/local-search concept. Prins (2009): directly relevant heterogeneous-fleet memetic methods. Vidal (2022): reference HGS implementation and richer local search; our code is NOT HGS. Zhao et al. (2024): multi-trip time-dependent Split is evidence that richer scheduling needs a tailored decoder; our time matrices are static. Hvattum (2025): Split start choices are a candidate future experiment, not an implemented performance claim. See RESEARCH_AND_ALGORITHM.md for links and reading-status qualifications.

The original prototype was AI-assisted. This audit and these experiments are a basis for understanding and revising it, not evidence that every team member has already mastered the field. No novelty claim is established.

## Next iterations, in order
1. Freeze the common constraint model and data with PSO; check cost assumptions and actual merge state.
2. Finish live ORS ingestion with agreed coordinates/profile if required, or explicitly approve the documented local graph approximation.
3. Improve hard-policy load balancing, cost/time-aware Split and local neighborhoods. Long schedules remain a limitation even when overtime is paid.
4. Compare seeded and unseeded runs, diversity counts, relocation/swap moves and restarts over multiple held-out instances. Only keep changes supported by experiments.
5. Compare PSO and compatible external methods under the same evaluator and budget; present limitations and future research directions.
