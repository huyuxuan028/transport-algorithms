# Proposed shared benchmark contract — pending both teams' agreement

This is a proposal, not a record of completed coordination.

1. Adopt ONE authoritative input dataset from the shared data work. Reuse its demands and customer IDs. The Budapest scenario supplied here is a geographic enrichment demonstration, not a replacement the GA team imposes on the PSO team.
2. Freeze instance SHA-256, raw OSM/ORS response hashes, graph/profile, coordinate provenance, matrix units, physical vehicle inventory, scenario parameters and all hard/soft constraints. OSM snapshots are ODbL; preserve attribution and source availability.
3. Use the same directed distance matrix in metres and the same duration matrix in seconds. A->B may differ from B->A. Never silently symmetrize. Either both teams use local graph matrices or both use the same ORS matrices; do not mix providers in one comparison.
4. Proposed baseline objective: fuel + maintenance + regular/overtime wages. Regular threshold 8 h; overtime multiplier 2. Per-vehicle wages and fuel prices are assumptions unless independently sourced and agreed. Coverage, per-trip weight/volume, fixed fleet and nonoverlap are hard. Decide whether 10–50 stops is hard; this package provides separate hard and soft scenarios. Decide whether five vehicles are available or must all be used. The fixed 1/2/2 inventory is the benchmark scenario, not a newly claimed supervisor instruction.
5. Decide whether aggregate volume with 10% reserve is the accepted loading model. If geometric packing, daily horizon, rest, reload time or truck restrictions are required, add them before calling the solution complete. Do not invent legal driver rules as course requirements.
6. Both methods export the same route-plan schema. One agreed evaluator recomputes coverage, capacities, times, overtime and cost independently of the search. Test evaluator invalid-route rejection together.
7. Development: seeds 0–4. Held-out evaluation: pre-agreed unseen seeds and instances; do not tune on held-out results. Report per-run feasibility, objective, wall-clock, evaluations and convergence. Publish software/environment and graph retrieval provenance.
8. Fair comparison: choose either equal wall-clock budgets or separately report both time and evaluation counts; decoder work is algorithm-dependent. Count initialization and repair evaluations. Exclude one-time road preprocessing from solver runtime but report it separately.
9. No optimum: report raw cost or improvement over a named valid baseline. Do not label it an optimality gap without a same-problem certified reference. Never compare soft-policy cost to hard-policy cost as if they solve the same problem.
10. Shared changes: one feature branch per person, PR review by another member, then merge. Record decisions and links; each person can explain the whole solver.

## Proposed coordination, without assigning work on others' behalf
- User: GA representation/operators, map/road adapter, experiment reproducibility; explain all operators.
- Dorina: review finance and overtime semantics; verify evaluator against independent examples.
- Subhan: review figures, convergence diagnostics and experiment protocol.
- PSO team: confirm authoritative data and shared evaluator/interface; exchange results under the same contract.
- Everyone: read the core sources, review a teammate's PR, and rehearse a whole-project explanation.

Suggested order: agree contract -> reconcile PRs -> freeze data and evaluator -> run both methods -> update findings -> rehearse. Record actual agreements and contributions as they occur, not retrospectively invented meetings.
