# Supervisor requirements and current evidence

| Requirement | Evidence | Remaining work |
|---|---|---|
| Repositories and review | Separate code PR #5 and research PR #6 in transport-algorithms; generator and findings repositories retained | Teammates review changes; keep final findings synchronized after merge |
| Collaboration | Adopt PSO team's customers, vehicle fleet and parameters; reuse Subhan's updated importer | Agree checksum, stop policy, snapping and evaluation budget with PSO; do not build a second independent dataset |
| Road distances at intended scale | 251x251 directed road distance/time matrices for the unchanged shared coordinates across Budapest; all pairs reachable | Local graph is simplified; ORS adapter exists but no ORS key/live run was available |
| Complete constraints | Exact coverage, fixed available fleet, repeated depot trips, capacities, reserve, service time and overtime; hard 10–50 test scenario | Obtain agreement on exclusions; no realistic working-day/rest feasibility claim |
| Convergence | 25 fresh shared-road runs: five seeds per variant, histories and diversity diagnostics; all valid under implemented model | One instance does not establish broad reliability or good final quality |
| Research/design | Explain permutation/allocation, distance-optimal contiguous Split, directed 2-opt, seeding and ablations | Each member must read sources and explain mechanism; integrate Subhan's forthcoming references |
| Presentation | New results and clear limitations, shared-city route map and reproducible commands | Team rehearsal and each member's understanding remain human tasks |

The old 1km² Keleti scenario is an early prototype, not the shared benchmark.
Old Keleti figures and costs are not relabeled as shared-data experiments.
PR #4 has already merged; its old conflict warning is obsolete. No grade is promised.

The strongest unresolved modeling issue exposed by the current run is unbounded
work duration: the best main-GA solution's longest vehicle span is 51.17 hours.
Paying overtime makes that schedule costed, not a credible single working day.
Before claiming a realistic complete solution, agree whether the planning horizon
is multiple days and implement the corresponding day/rest constraints, or agree
a finite shift horizon. The instructor's overtime allowance alone specifies neither.
