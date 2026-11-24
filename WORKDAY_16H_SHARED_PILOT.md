# Shared Budapest 16-hour GA pilot

Compared original GA and relocate-only GA on preselected small, middle and large address subsets (IDs 000, 049, 099). This is a GA-only pilot, not a GA-versus-PSO result. The archive contains three instances; the 100-case manifest is provided only for provenance.

| Addresses | Mean original objective (EUR) | Mean relocate-only objective (EUR) | Relocate minus original (EUR) | Mean original penalty (EUR) | Mean relocate penalty (EUR) |
|---:|---:|---:|---:|---:|---:|
| 150 | 825.58 | 882.10 | 56.52 | 0.00 | 0.00 |
| 199 | 1,223.22 | 103,511.48 | 102,288.27 | 0.00 | 102,000.00 |
| 249 | 251,856.11 | 235,856.74 | -15,999.37 | 250,000.00 | 234,000.00 |

Original GA wins all paired runs on the 150- and 199-address cases; relocate-only GA wins all paired runs on the 249-address case. On 199 addresses the original GA reached a zero-penalty plan in all three seeds, but relocate-only retained a substantial short-trip penalty. The comparison evaluates allocation of a fixed combined budget: the relocate arm spends part on local trials and consequently evaluates fewer GA candidates. These runs do not isolate which allocation would win at equal GA candidate counts.

All 18 final schedules passed validation. Each pair shared an explicitly validated initial plan filtered from the prior 250-address GA solution. The original suite reference plans are historical and are not used as capped feasible starts. The filtered plan method was separately verified across all 100 suite instances; that is not a 100-instance solver run.

Population 32, seeds 0/1/2, maximum 200 generations, 6,032 combined counts per run, with up to 40 relocate trials per generation in the relocate arm. This is a shared counting rule, not equal computation per trial. Runtime is descriptive because different cases ran concurrently. All costs include the published soft-stop penalty.

The experimental inputs match their committed SHA-256 values. Explicit sequential floating-point accumulation for the historical reference schedules restores v1 byte compatibility across Python versions, without changing GA search or the tracked manifest.

To reproduce from the repository root after applying the changes:

```bash
python build_workday_suite.py
python run_workday_shared_pilot.py --output results/workday_16h_shared_pilot_reproduction
```

For a cross-team evaluator check, score the three supplied initial plans on their matching instance bytes and compare with fixed_plan_ga_scores.json. Confirm capacity semantics, shifts, overtime rates, and penalty settings before making GA-versus-PSO claims.
