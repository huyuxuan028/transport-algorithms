# Supervisor requirements and evidence

This package is a local candidate for review, not an approved milestone or a merged release. A grade is determined by the supervisor; no grade is promised. The written requirement for a complete solution supersedes treating known constraint gaps as finished work.

| Requirement | Evidence supplied | Remaining acceptance work |
|---|---|---|
| All repositories visible | Three repository-specific folders and change notes; current GitHub main files audited | Reconcile open PR #4, currently not automatically mergeable; review/merge changes and provide all repo links |
| Collaboration within and between teams | Shared benchmark contract and proposed responsibilities | Both teams must actually agree and record the chosen data, constraints and budget. A document alone is not collaboration |
| Complete agreed model | Coverage, capacity, buffered volume, fixed fleet, repeated nonoverlapping trips, overtime cost; optional hard stop decoder and validator | Decide which constraints are binding. Geometric packing, rest rules and truck-specific road access are not implemented and cannot be described as satisfied |
| Intended scale | Real Budapest OSM graph scenario with 250 orders and five available physical vehicles | Jointly confirm that this is the required scale; repeat on other shared instances |
| Stable convergence | Five-seed traces, range bands, costs, runtimes, feasibility and diversity diagnostics | Small exploratory experiments do not establish robust convergence across unseen instances |
| Research and deliberate design | Literature map, source links, decision log and nearest-neighbor initialization experiment | Each person must read/understand the sources and defend decisions independently |
| Acceptable presentation | English narrative, Q&A and figure checklist | Rehearse and use the approved shared run, not stale plots or mixed policies |

## Current repository inconsistencies
- Algorithms main solver blob d17f583360f976510e74ef88373f245a7aa3a79d still requires symmetric distances and schedules with one shared speed. Its README discusses optimizing the fleet mix even though the fixed benchmark freezes it.
- Generator main README blob b59c3fdec95aff225d256fdad369f5bcab20968a explains aggregate capacities and soft stop audits; it does not supply real road distances.
- Findings main README blob dfe513e2da0f4bcde1d1bbacdbbad1c23d647d24 still describes fuel as a proposed default and no wage coefficients; this conflicts with the cost objective already implemented elsewhere.
- PR #4 is open and mergeable=false as returned by GitHub during this audit. Do not delete main files or overwrite a teammate's branch to resolve it.

## What is real in the Budapest scenario?
Raw street geometry and connectivity come from the official OSM API around Keleti (19.075,47.495,19.085,47.505 west/south/east/north). The raw XML and converted node/way snapshot are included. The graph has 561 nodes with permitted supported highway classes; the depot's mutually reachable component has 474 nodes. One-way and basic motor access tags are applied. The depot and 250 delivery points are simulated road nodes; furniture demands are copied unchanged from the existing benchmark. These are not observed customer addresses or actual shipments. Map availability does not establish parking or unloading access.

Travel times are explicit road-class speed assumptions, optionally capped by numeric maxspeed tags. Dijkstra minimizes estimated time and records distance along that same path. Thus durations and distances describe the same route. These are not measured traffic times. Turn relations, signals, HGV constraints and routes outside the downloaded graph are missing. A finite local graph can overestimate or distort routing.

The road map in this package has actually been generated from downloaded data and actual solver routes. ORS integration is a separate implementation and has not been live-tested without an account key. Do not call local OSM routing an ORS result.

## Minimum presentation gate
Do not say 'all constraints are incorporated' until the shared contract identifies which requirements are hard, soft, excluded or pending, with explicit team/supervisor agreement. The optional hard 10–50 scenario can still have long driver schedules under the unlimited-horizon model. Paying overtime is not equivalent to modeling realistic rest/day constraints. The strongest honest status is: working expanded prototype with traceable evidence and explicit remaining scope decisions.
