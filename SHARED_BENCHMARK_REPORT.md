# Shared Benchmark: PSO 100-Instance Integration & Distance Matrix Alignment

**Author**: Dorina (`H-Dorina`)  
**Branch**: `feature/H-Dorina/pso-100-benchmark-cross-eval`  
**Reference Tasks**: Task 3 (Shared benchmark with PSO) & Task 4 (Consolidated team markdown prep) from `_notes_symlink/remaining(transport-algorithms).md`.

---

## 1. Context and Scrum Discussion: Distance Metric Alignment

During our team scrum, the following architectural difference was highlighted:
- **GA team (`transport-algorithms`)**: Generates and optimizes over asymmetric OpenStreetMap road-network distance and duration matrices (`distance_matrix_m` and `duration_matrix_s`, e.g., Budapest road network with one-ways and speed assumptions).
- **PSO team (`industrial-transport`)**: Uses haversine distance with a `1.3` winding factor (`distances.csv`, symmetric off-diagonal) across all its generated test instances (`test_3001..test_3100`), where driving duration is computed from distance divided by per-vehicle `avg_speed_kmh`.

### The Core Question
> Should GA support haversine straight-line / winding distance alongside road network distance, or should one distance metric be standard for the shared 100-instance comparison?

### Code Reality & Solution in this PR:
1. `solver.py` in `transport-algorithms` already handles both cleanly:
   - If `duration_matrix_s` is present (road instances), `solver.travel_minutes` uses actual road durations.
   - If `duration_matrix_s` is absent (such as in PSO's `distances.csv`), `solver.travel_minutes` falls back to `distance_matrix_m` divided by vehicle `speed_kmh`.
2. `import_pso_dataset.py` imports PSO's exact haversine×1.3 `distances.csv` into `distance_matrix_m` (in meters).
3. Therefore, **GA can run on PSO's exact straight-line/winding distance metric today without modifying the core GA solver**.
4. Both options remain open for the team:
   - **Recommendation**: Support straight-line/winding distance for direct, apple-to-apple comparison with the PSO team on the 100 test instances (`test_3001..test_3100`), while retaining GA's road network capabilities as an extension.

---

## 2. Work Implemented in this PR

1. **Updated Dataset Importer (`import_pso_dataset.py`)**:
   - Accepts arbitrary instance directories directly (e.g., `instances/test/test_3001` or root `dataset/`).
   - Makes `best_solution.json` optional (`--pso-solution`), enabling import of instances without pre-existing PSO solution files.
   - Preserves instance metadata (`seed`, `name`, and PSO's `day_start`, `last_delivery_by`, `hard_day_end`).
   - Adds batch import (`--batch-source <dir> --batch-output <dir>`) with automated SHA-256 manifest generation.
   - Tested: all 100 test instances (`test_3001..test_3100`) pass GA `validate_instance` and neutral witness schedule generation.

2. **Bidirectional Cross-Evaluator (`cross_evaluate_pso.py`)**:
   - **PSO Plan -> GA Evaluator**: Translates PSO trip customer allocations into GA schedules and runs `solver.validate_solution`.
   - **GA Plan -> PSO Evaluator**: Translates GA transports into PSO `TripPlan`/`Solution` objects and runs PSO's `trip_metrics`, `day_metrics`, and `check_solution`.
   - Dynamic path discovery without hardcoded local machine paths.

3. **Cross-Evaluator Parity Verification (Measured Results)**:
   - **PSO Seed 42 Plan** (`industrial-transport/output/best_solution.json`):
     - PSO Reported `true_cost_eur`: `1186.2604`
     - GA Evaluator `real_cost_eur`: `1186.2604`
     - Difference: `< 0.0001 EUR` (exact match)
   - **PSO Test 3001 Plan** (`industrial-transport/output/test_3001/best_solution.json`):
     - PSO Reported `true_cost_eur`: `1263.4175`
     - GA Evaluator `real_cost_eur`: `1263.4175`
     - Difference: `< 0.0001 EUR` (exact match)
   - **GA Neutral Witness on Test 3001**:
     - GA Evaluator `real_cost_eur`: `1415.7453`
     - PSO Evaluator Base + Overtime Cost: `1415.7453`
     - Difference: `< 0.0001 EUR` (exact match)

4. **Automated Unit Tests (`test_cross_evaluator.py`)**:
   - 7 unit tests covering single import, optional solution handling, batch conversion, and bidirectional evaluator parity.
   - All 60 unit tests in `transport-algorithms` pass cleanly.

---

## 3. Day-Rule Alignment Note for the PSO Team

| Rule | GA Implementation (`solver.py`) | PSO Implementation (`industrial-transport`) |
|---|---|---|
| Shift Length | 8.0 h (480 min) | 8.0 h (480 min) |
| Overtime Multiplier | 2.0x regular wage | 2.0x regular wage |
| Min / Max Stops | Min 10 (soft, 2,000 EUR/missing), Max 50 (hard) | Min 10 (soft, 2,000 EUR/missing), Max 50 (hard) |
| Day Horizon | Single bound: 16.0 h (960 min, 08:00–24:00) | `hard_day_end: 23:00` (15 h / 900 min) + `last_delivery_by: 22:00` (14 h / 840 min) |

We are ready to cross-score plans under whichever day-rule option both teams agree upon once GA's post-fix runs on the 100 instances are produced.
