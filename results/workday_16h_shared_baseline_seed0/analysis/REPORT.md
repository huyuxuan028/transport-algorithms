# Budapest shared suite — GA baseline, seed 0

All 100 final schedules were feasible. Compared with the supplied initial
schedule for each case, the penalty-inclusive objective decreased in **53**
cases, was unchanged in **47**, and increased in **0**. All 100 initial
schedules had a penalty. **52** finished with zero penalty, and **48** still
had a penalty. The median per-case reductions were
**€244.08** in operating cost,
**€219,000.00** in soft penalties and
**€219,336.62** in the total objective.
These medians were computed separately.

| Addresses (25 cases per group) | Objective lower | Unchanged | Higher | Penalty went to zero | Median objective reduction (EUR) |
|---|---:|---:|---:|---:|---:|
| 150-174 | 25 | 0 | 0 | 25 | 266,323.61 |
| 175-199 | 22 | 3 | 0 | 22 | 258,312.53 |
| 200-224 | 6 | 19 | 0 | 5 | 0.00 |
| 225-249 | 0 | 25 | 0 | 0 | 0.00 |

Improvements were concentrated below 200 addresses. None of the 25 cases
with 225–249 addresses improved on their supplied initial objective in this
run.

The per-case comparison uses the supplied initial schedule recorded in
`baseline_decoded.cost` and the final validated costs. The convergence
panel uses the saved best objective at each generation, scaled to that
case's generation-0 best. Case 003 (153 addresses) already had a better
candidate at generation 0 (€59,432.4431) than its supplied initial schedule
(€267,205.7400), so its two starting points differ. The lower panel plots
the supplied-to-final objective reduction for every instance. All requested
costs and all 201 generation records per case were present.

These statements describe the original run records inspected during the
analysis. The baseline `cases/*.json` records are retained locally and are
not included in this PR. Paths to those records in the top-level trace CSV
are provenance text, not links to files supplied by this PR. This PR includes
the analysis tables and figure linked below, along with the baseline summary,
configuration and aggregate statistics.

The [reproduction commands](../../../WORKDAY_16H_BENCHMARK.md#reproduction-commands)
cover instance generation and solver runs, which produce new checkpoints
and baseline summaries. They do not automatically generate the three
analysis CSVs, `convergence.svg` or this analysis report; those are supplied
analysis outputs.

[Per-case cost comparison](initial_vs_final.csv) ·
[Remaining penalty cases](remaining_penalties.csv) ·
[Size-group statistics](size_groups.csv) ·
[Convergence and final improvement](convergence.svg)
