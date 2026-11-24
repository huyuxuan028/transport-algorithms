# Budapest 250 cross-trip search

This experiment compares the original cost GA with the same GA plus
`relocate` and `swap`. It uses the frozen Budapest 250-address directed road
matrices, fixed five-vehicle fleet and 960-minute workday. The feasible
starting routes are taken verbatim from the
[previous seeded run](results/workday_16h_seed_comparison/seeded.json).
Trips may serve at most 50 customers. Trips with fewer than 10 customers
incur €2,000 per missing stop.
Both arms independently validate these routes and place them as one candidate
in generation 0. The other 31 initial chromosomes use the same RNG stream
within each seed pair. At generation 0, the incumbent operating cost is
€1,860.5025, with 19 short trips, a €250,000 penalty, a €251,860.5025 score
and a longest vehicle day of 958.78 minutes.

## Operators and acceptance

`--relocate` and `--swap` can be enabled individually or together on the
cost GA. Both are off by default. After each generation, the enabled moves
search the best feasible incumbent. An accepted schedule enters the
population, where it can survive as an elite and supply its updated customer
order and vehicle assignments to offspring. Offspring still use Split.

- **Relocate** removes one customer from a source trip and inserts it at a
  specified position in a distinct destination trip, on the same or a
  different physical vehicle. An emptied source trip is removed. For
  example, moving the sole customer of a 1-stop trip into an 8-stop trip
  leaves one 9-stop trip and reduces the combined stop shortfall from 11
  to 1. Enumeration first favors a reduction in the number of short trips,
  then a lower predicted stop shortfall and pairs involving a short trip.
  It skips route pairs that cannot meet
  the hard stop bounds or whose destination cannot accommodate even the
  smallest customer from the source by usable volume.
- **Swap** exchanges two customers at their existing positions in distinct
  trips, including cross-vehicle exchanges. Trip lengths stay the same, so
  the move cannot directly reduce the stop penalty. It prioritizes pairs
  involving a short trip and can improve distance, wages or capacity
  distribution. Both neighborhoods use same-vehicle preference and proximity
  of the first stops to break ties in their route-pair ordering.

For each emitted move, the solver copies the affected routes and reschedules
**all trips on each affected vehicle** from minute zero. It recalculates
directed travel, loading and unloading service, and each later trip's start
and finish. For example, a vehicle finishing after 540 minutes has 60 minutes
at double wages. If an exchange cuts its day to 510 minutes, only 30 minutes
are at double wages. The receiving vehicle's overtime can also change, so
neither the changed trip's duration nor the change in total fleet minutes
alone gives the correct wage delta.

Each trial is repriced for fuel, wages, maintenance and the soft penalty,
including proposals the validator rejects. The validator checks payload,
usable volume, exact-once coverage, hard stop bounds, nonoverlap and the
960-minute return deadline.
The move enters the population only if the validator accepts it and its
penalty-inclusive score strictly decreases. The implementation covers the two
single-customer neighborhoods described above.

## Budget and complexity

Both arms are capped at 6,032 **counted operations**, starting with the 32
initial candidates. A chromosome evaluation, including its existing Split,
within-trip 2-opt and repairs, counts once. A cross-trip proposal that is
scheduled and submitted to the validator also counts once, whether it is
rejected, valid but nonimproving, or accepted. Structural route-pair exclusions
and ordering do not submit a proposal. The arms share a count cap and use
different mixes of work, so the report gives both counts and elapsed time.
The enhanced arm gets up to 40 trials after a generation, alternating
operators when both have proposals. It resumes enumeration on an unchanged
incumbent and rebuilds the neighborhood after an incumbent change. The
combined cap can end its run before generation 200.

Let `n` be customers, `T` be nonempty trips, `V` be vehicles and `n_A`
be stops assigned to the one or two affected vehicles. Each neighborhood
contains at most `O(n²)` concrete proposals. For relocate, this follows from
counting source stops and destination insertion positions. For swap, it
follows from counting pairs of stops in distinct trips. On each incumbent
change, building and sorting the route-pair lists costs
`O(n + T² log T)` time and `O(n+T²)` auxiliary space. Concrete proposals are
generated lazily. Rescheduling takes `O(n_A + V)` time. The full validation
and price calculation per proposal take `O(n log n + VT)` in the worst
case, including sorting visits, checking route legs and aggregating trips by
vehicle. The benchmark has `n=250` and `V=5`.

For `B_GA` chromosome evaluations, `B_local` local trials and `R` neighborhood
builds, the local addition costs
`O(R(n + T² log T) + B_local(n log n + VT))`, using the maximum trip count
for `T`. The original `B_GA` chromosome evaluations keep their existing
Split, local reversal and repair costs. Both stages and initialization are
included in the measured search runtime. Final verification and artifact
writing are outside that timer.

## Results

All six final schedules passed validation. Each enhanced run improved the
operating cost and total score by €38.7192. The stop penalty, count of 19
short trips, and longest vehicle workday were unchanged.

| Seed | Arm | Final generation | GA candidates | Cross-trip trials | Search seconds | Operating cost (€) | Penalty (€) | Total (€) | Short trips | Longest vehicle (min) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | Original | 200 | 6,032 | 0 | 37.36 | 1,860.5025 | 250,000 | 251,860.5025 | 19 | 958.78 |
| 0 | Relocate + swap | 86 | 2,612 | 3,420 | 18.29 | 1,821.7833 | 250,000 | 251,821.7833 | 19 | 958.78 |
| 1 | Original | 200 | 6,032 | 0 | 39.90 | 1,860.5025 | 250,000 | 251,860.5025 | 19 | 958.78 |
| 1 | Relocate + swap | 86 | 2,612 | 3,420 | 17.96 | 1,821.7833 | 250,000 | 251,821.7833 | 19 | 958.78 |
| 2 | Original | 200 | 6,032 | 0 | 38.53 | 1,860.5025 | 250,000 | 251,860.5025 | 19 | 958.78 |
| 2 | Relocate + swap | 86 | 2,612 | 3,420 | 18.63 | 1,821.7833 | 250,000 | 251,821.7833 | 19 | 958.78 |

In each enhanced run, all 1,710 relocation trials failed validation. Of
1,710 swap trials, 178 were valid and 17 lowered the incumbent score and
were accepted. The observed gain came entirely from swaps. These results
cover three seeds on one instance and one common starting schedule.

[Convergence chart](results/workday_16h_cross_trip_comparison/convergence.svg),
[generation CSV](results/workday_16h_cross_trip_comparison/convergence.csv),
[per-run summary](results/workday_16h_cross_trip_comparison/summary.csv) and
[full JSON outputs](results/workday_16h_cross_trip_comparison).

## Reproduce

From the repository root, use a new output directory.

```powershell
python -m unittest discover -v
python run_workday_cross_trip_comparison.py --output generated/workday_16h_cross_trip_comparison
```

The dedicated tests cover the two independent switches, combined-budget
accounting, cross-vehicle relocation and exchange, removal of an emptied
trip, rejection of a cost tie, whole-day wage recomputation, and rejection
when a later trip would return after midnight. The full suite had 47 passes and two skips because
Matplotlib was unavailable. The runner generates its SVG with the Python
standard library.
