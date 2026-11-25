# Budapest 250 relocate diagnostics and operator ablation

This follow-up preserves the [previous combined-operator run](WORKDAY_16H_CROSS_TRIP_COMPARISON.md).
It compares original GA, swap-only GA and relocate-only GA at seeds 0, 1
and 2 on the same frozen Budapest 250 road instance. The arms start from
the same validated workday schedule and use the same random initialization
for the other 31 candidates within each seed.

## How rejection reasons are counted

Each emitted relocate proposal is scheduled, validated and repriced. A
rejected proposal contributes one reason. On a hard failure the reason is
the first check that failed in the existing validator order. Multiple
violations in the same proposal therefore do not inflate the counts.

| Reason | Meaning |
|---|---|
| `payload` | A trip exceeds its vehicle's payload |
| `usable_volume` | A trip exceeds usable volume after the reserve |
| `max_stops` | A trip exceeds the hard maximum of 50 stops |
| `workday_horizon` | Recomputed cumulative work exceeds 960 minutes |
| `coverage` | An invalid, missing or repeated customer visit |
| `empty_trip` | An empty trip remains in the submitted schedule |
| `min_stops` | A configured hard minimum is violated. Budapest uses a soft minimum |
| `no_improvement` | Validation passed, but the total including penalties did not decrease |
| `other_validation` | Another validator check failed |

The destination stop bound and minimum possible inserted volume can also
rule out an entire source/destination pair before it emits a proposal.
Those checks, plus the hard source minimum where enabled, have separate
`screened_pairs_*` columns. They are counts of ordered route pairs screened
across neighborhood builds, so a pair may be counted again after the
incumbent changes. Screened pairs do not consume local trial budget.
Successful removal of an emptied source trip is normal and is not an
`empty_trip` rejection.

## Hand-built acceptance check

The fixture has a one-stop trip on vehicle 0 and an eight-stop trip on
vehicle 1. Each of the nine customers requires 20 minutes of service and
0.25 kg and m³ of capacity. Travel is zero to isolate the move. With the
10% volume reserve and the same 10-soft, 50-hard and 960-minute rules,
moving the single customer into the eight-stop trip gives vehicle 1 a
nine-stop trip lasting 180 minutes. Vehicle 0 becomes idle. Both schedules
pass the full validator, and the real cost stays €60. The penalty drops
from €22,000 to €2,000, so relocate accepts the first proposal. The
coverage and empty-trip checks are tested separately.

## Budapest results

All nine final schedules passed revalidation. Within each arm, all three
seeds ended with the same costs, stop counts and longest workday.

| Arm | GA evaluations per run | Local trials per run | Operating cost (€) | Penalty (€) | Total (€) | Short trips | Longest workday (min) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original | 6,032 | 0 | 1,860.5025 | 250,000 | 251,860.5025 | 19 | 958.78 |
| Swap only | 2,612 | 3,420 | 1,817.1818 | 250,000 | 251,817.1818 | 19 | 958.78 |
| Relocate only | 2,612 | 3,420 | 1,861.1303 | 234,000 | 235,861.1303 | 18 | 959.71 |

| Seed | Original (s) | Swap only (s) | Relocate only (s) |
|---:|---:|---:|---:|
| 0 | 49.80 | 24.17 | 20.66 |
| 1 | 39.44 | 22.04 | 18.73 |
| 2 | 39.17 | 18.52 | 19.37 |

Each relocate-only run accepted 8 of 3,420 trials. There were 3,256
workday rejections and 156 usable-volume rejections. Payload, maximum
stops, coverage, empty trip, hard minimum, no improvement and other
validation all recorded zero. Volume also screened out 2,511 ordered
route pairs per run before trial generation. No pairs were screened out
for stop bounds. Each swap-only run accepted 22 trials and saved €43.3207
in operating cost. Relocate-only saved €15,999.3722 in the total objective.

The acceptance test and the eight accepted moves per relocate-only run
show that the relocation path works under the existing rules. The timing
and volume counts show how restrictive the current schedules are. The
previous combined run spent half of its local trials on swap, and accepted
swaps changed the incumbent and restarted neighborhood enumeration. It
therefore explored a different sequence of relocation trials.

[Run summary](results/workday_16h_isolated_operators/summary.csv) ·
[Rejection counts](results/workday_16h_isolated_operators/relocate_rejections.csv) ·
[Convergence chart](results/workday_16h_isolated_operators/convergence.svg)

## Reproduce

From the repository root, use a new output directory.

```powershell
python -m unittest discover -v
python run_workday_cross_trip_comparison.py --isolated-operators --output generated/workday_16h_isolated_operators
```

The three arms use the same combined cap of 6,032 counted operations.
A GA candidate and a fully evaluated cross-trip proposal each debit one
unit, though they have different costs. The operator arms can use up to 40
local trials per generation. The run writes individual JSONs,
`summary.csv`, `relocate_rejections.csv`, `convergence.csv`, and
`convergence.svg`. The test suite had 51 passes and two skips for missing
Matplotlib.
