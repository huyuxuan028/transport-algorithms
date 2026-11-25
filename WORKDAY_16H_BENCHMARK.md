# Budapest 16-hour workday benchmark

## Scope and protocol

The shared Budapest suite contains 100 frozen road instances with 150–249
addresses. The original GA baseline uses seed 0 across the full suite.
The two multi-seed blocks contain six case entries across **five distinct
instances**. The pilot covers 000, 049 and 099. The large-instance check
covers 074, 075 and 099. Case 099 appears in both and is counted once when
describing distinct cases. The final paired block covers 075–099 at seed 0.
These blocks overlap and some checkpoints are reused.

Both GA arms use the same verified supplied schedule within each pair,
population 32, up to 200 generations, a 6,032 combined-count ceiling and
swap disabled. The hard rules include capacity, exact-once coverage, at most
50 stops per trip and return by 960 minutes. The operating cost covers fuel,
wages and maintenance. The soft minimum of 10 stops costs EUR 2,000 per
missing stop. The total objective adds the soft penalty to operating cost.

## Hard feasibility and costs

All runs in the following blocks passed final validation. The cost columns
are arithmetic means of the saved per-run CSV values.

| Block | Arm | Hard-feasible | Operating (EUR) | Soft penalty (EUR) | Total objective (EUR) | Zero penalty |
|---|---|---:|---:|---:|---:|---:|
| Full suite, seed 0 | Original | 100/100 (100%) | 1,340.64 | 119,220.00 | 120,560.64 | 52/100 |
| Pilot, seeds 0–2 | Original | 9/9 (100%) | 1,301.64 | 83,333.33 | 84,634.97 | 6/9 |
| Pilot, seeds 0–2 | Relocate only | 9/9 (100%) | 1,416.77 | 112,000.00 | 113,416.77 | 3/9 |
| Large check, seeds 0–2 | Original | 9/9 (100%) | 1,760.71 | 252,000.00 | 253,760.71 | 0/9 |
| Large check, seeds 0–2 | Relocate only | 9/9 (100%) | 1,707.52 | 164,000.00 | 165,707.52 | 0/9 |
| 075–099, seed 0 | Original | 25/25 (100%) | 1,778.96 | 252,240.00 | 254,018.96 | 0/25 |
| 075–099, seed 0 | Relocate only | 25/25 (100%) | 1,730.96 | 147,600.00 | 149,330.96 | 0/25 |

The multi-seed case means below use seeds 0, 1 and 2. Both case-099 blocks
gave the same final costs for every seed and arm.

| Case | Addresses | Original operating / penalty / total (EUR) | Relocate operating / penalty / total (EUR) | Lower total in all three pairs |
|---|---:|---|---|---|
| 000 | 150 | 825.58 / 0.00 / 825.58 | 882.10 / 0.00 / 882.10 | Original |
| 049 | 199 | 1,223.22 / 0.00 / 1,223.22 | 1,511.48 / 102,000.00 / 103,511.48 | Original |
| 074 | 224 | 1,692.99 / 246,000.00 / 247,692.99 | 1,574.93 / 128,000.00 / 129,574.93 | Relocate |
| 075 | 225 | 1,733.01 / 260,000.00 / 261,733.01 | 1,690.90 / 130,000.00 / 131,690.90 | Relocate |
| 099 | 249 | 1,856.11 / 250,000.00 / 251,856.11 | 1,856.74 / 234,000.00 / 235,856.74 | Relocate |

Relocate-only had **25 wins, zero ties and zero losses** in the paired
**225–249-address, seed-0** block. The median paired penalty reduction was
**EUR 124,000** and neither arm reached zero penalty in this block. The
original arm used 6,032 GA evaluations per run. Relocate-only used 2,612
GA evaluations and 3,420 local trials. The shared cap assigns one count per
operation. Candidate evaluations and local trials have different per-operation
costs. Mean recorded runtimes were 115.86 s and 46.27 s, respectively.
The records come from different batches with parallel workers and retain
the original timings for reused runs. The timing means are descriptive.

## What the generation records show

- **Full-suite original GA.** The supplied initial objective improved on
  cases 000–043, 047–050, 054–055, 057, 060 and 062 (53 cases). The other
  47 cases retained their exact supplied routes and had flat best-objective
  traces. All 52 final zero-penalty cases started with a positive penalty.
  On case 003, generation 0 was already below the supplied schedule.
- **Multi-seed blocks.** Original GA improved on 000 and 049 at every seed.
  All original runs on 074, 075 and 099 retained their exact supplied
  routes. Relocate-only improved on all five distinct cases at every seed
  relative to the supplied start. Its first improvement was at generation
  1 on 000, 049, 074 and 075, and at generation 8 on 099. On 049, original
  GA first improved at generations 134, 136 and 151 for seeds 0, 1 and 2,
  and ended at zero penalty each time. Relocate-only made earlier progress
  on 049 and finished with EUR 102,000 in penalties each time.
- **075–099, seed 0.** All 25 originals retained their supplied routes
  through the final generation. All 25 relocate-only runs improved,
  first at generations 1–8, with their last strict improvements at
  generations 29–85.

The [trace audit](WORKDAY_16H_BENCHMARK_TRACE.csv) records each run's source
checkpoint path and gives the supplied objective, generation-0 objective,
first generation below the supplied start, last strict improvement after
generation 0, and whether the routes were retained. A blank first-improvement
field means that the supplied objective was never beaten. A zero
last-improvement field means that no strict decrease occurred after
generation 0. CSV cost and feasibility fields were checked against the saved
validation blocks, and each final trace objective was checked against its CSV.

The `source_checkpoint` column preserves the paths of the original run
records used for this audit. The raw run JSONs for the three new result
directories are retained locally and are not included in this PR. These
paths are provenance text, not links to files supplied by this PR; a fresh
checkout cannot use them to inspect those original schedules or full
generation histories. The existing pilot records are already tracked and
remain available. The trace CSV is a supplied audit summary, not a substitute
for the omitted original records.

Source summaries
[100-case baseline](results/workday_16h_shared_baseline_seed0/summary.csv) ·
[pilot](results/workday_16h_shared_pilot_local/summary.csv) ·
[large multi-seed comparison](results/workday_16h_large_paired/summary.csv) ·
[25-case paired comparison](results/workday_16h_large_seed0/summary.csv)

## Reproduction commands

Run from the repository root in PowerShell. Use fresh output directories.
The two later runners can reuse verified checkpoints at their standard
`results/` paths when present. They run missing pairs when those caches are
unavailable. The commands cover instance generation and solver runs,
including the summaries written by the runners. This reporting pass only
read existing experiment results; it did not rerun the solvers.

```powershell
python build_workday_suite.py --output generated/shared_workday_16h_benchmark_repro
python run_workday_shared_pilot.py --instances generated/shared_workday_16h_benchmark_repro --cases 0 49 99 --output generated/benchmark_pilot_repro
python run_workday_shared_baseline.py --instances generated/shared_workday_16h_benchmark_repro --output generated/benchmark_baseline_repro --jobs 8
python run_workday_large_paired.py --instances generated/shared_workday_16h_benchmark_repro --output generated/benchmark_paired_repro --jobs 8
python run_workday_large_seed0.py --instances generated/shared_workday_16h_benchmark_repro --output generated/benchmark_large_seed0_repro --jobs 8
```

Some analysis outputs are supplied with this PR but are not automatically
generated by these commands: `WORKDAY_16H_BENCHMARK_TRACE.csv`, the baseline
`analysis/` CSVs, report and `convergence.svg`, and the large multi-seed
`paired_deltas.csv` and `REPORT.md`. The top-level benchmark report is also
maintained separately. The 25-case runner does generate its own
`paired_deltas.csv`, `totals.json` and `REPORT.md`. Thus the commands reproduce
the instance-generation and solving workflow, not every supplied analysis
table, figure or narrative report.

The baseline and 25-case runners support `--resume` with the original
output directory containing checkpoints from a prior run. The original
checkpoints omitted from this PR are not available for resume on a fresh
checkout. To exercise the checkpoint reuse workflow, first generate new
upstream checkpoints using the standard output names
`results/workday_16h_shared_baseline_seed0` and
`results/workday_16h_large_paired` for those two upstream runs.

## PR contents: 23-file selection

- Add `WORKDAY_16H_BENCHMARK.md`, `WORKDAY_16H_BENCHMARK_TRACE.csv`,
  `run_workday_shared_baseline.py`, `run_workday_large_paired.py` and
  `run_workday_large_seed0.py`.
- Include `summary.csv` and `run_config.json` from each of the three new
  result directories linked above, plus `paired_deltas.csv` from both paired
  directories. Include the baseline and 25-case `totals.json` and the
  multi-seed `reuse_decisions.json` as compact provenance.
- Include `REPORT.md` from both paired result directories and all five
  files in `results/workday_16h_shared_baseline_seed0/analysis/` (the report,
  three CSVs and `convergence.svg`).
- Keep the 168 raw run JSONs, three generated `*_initial_plan.json` copies
  and two empty failure records locally, outside this PR selection. The
  runners derive their initial schedules from the already tracked
  `results/workday_16h_seed_comparison/seeded.json`; the new initial-plan
  copies are outputs, not required reproduction inputs. Missing run
  checkpoints are regenerated by solving. The existing pilot is already
  tracked. Keep generated instance copies under `generated/`.
- Use `PR10_DESCRIPTION.md` only as the draft for updating the PR #10 web
  description; do not include it in the commit.
