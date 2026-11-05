# Supervisor requirements and current evidence

| Requirement | Evidence | Remaining work |
|---|---|---|
| Repositories and review | Separate code PR #5 and research PR #6 in transport-algorithms; generator and findings repositories retained | Teammates review changes; keep final findings synchronized after merge |
| Collaboration | Adopt PSO team's customers, vehicle fleet and parameters; reuse Subhan's updated importer | Agree checksum, stop policy, snapping and evaluation budget with PSO; do not build a second independent dataset |
| Road distances at intended scale | 251x251 directed matrices retained unchanged; stale embedded PSO-plan metrics rescheduled and validated | Local graph is simplified; ORS adapter exists but no live ORS run is claimed |
| Complete constraints | Revised branch uses soft minimum 10 with EUR 2,000 per missing customer and hard maximum 50, alongside capacity, reserve, coverage and overtime | Revised code needs separate review/merge; no realistic working-day/rest feasibility claim |
| Convergence | Subhan's 30-run pilot revalidated; five cost-GA seeds, population 32, 200 generations and 6,032 evaluations each | One instance and five cost-GA seeds do not establish broad reliability; historical hard-stop studies are distinct |
| Research/design | Explain permutation/allocation, distance-optimal contiguous Split, directed 2-opt, seeding and ablations | Each member must read sources and explain mechanism; integrate Subhan's forthcoming references |
| Presentation | New results and clear limitations, shared-city route map and reproducible commands | Team rehearsal and each member's understanding remain human tasks |

The old 1km² Keleti scenario is an early prototype, not the shared benchmark.
Old Keleti figures and costs are not relabeled as shared-data experiments.
PR #4 has already merged; its old conflict warning is obsolete. No grade is promised.

The old hard-stop run exposed unbounded work duration with a 51.17-hour vehicle
span. The new best cost-GA plan reduces the maximum to 18.69 hours, which still
does not establish a realistic working day.
Paying overtime makes that schedule costed, not a credible single working day.
Before claiming a realistic complete solution, agree whether the planning horizon
is multiple days and implement the corresponding day/rest constraints, or agree
a finite shift horizon. The instructor's overtime allowance alone specifies neither.


## Current acceptance evidence

The old 25-run,80-generation hard-stop evidence is historical. Subhan's revised
soft-stop pilot has 30 runs (three objectives, two methods, five seeds), with
32 individuals,200 generations and 6,032 evaluations per run. HU revalidated all
30 saved plans; the five cost-GA runs have mean real cost EUR 1,473.39, best
EUR 1,461.07, sample SD EUR 7.45 and zero penalties. This is artifact verification,
not a second independent GA execution. The soft-repair source branch requires
separate code review/merge; this documentation PR does not merge its code.

The fixed PSO-team plan was rescheduled on the road matrices: real cost
EUR 1,472.0597 and overtime 28.4723vehicle-hours. Its customer ordering and vehicle
assignments were not reoptimized. The corrected attachment changes the PSO audit
block only; a new whole-file hash and unchanged-matrix checks are supplied.

Before merge: review the six updated docs, verify the pilot source commit and
corrected-road checksum, and have a teammate review the reference audit.
Do not treat a fixed-plan reference comparison as a new multi-seed PSO benchmark.
