# Shared Budapest road benchmark workflow

This code replaces the local Keleti demonstration with the original shared
PSO-team address set. It generates no new orders or customer locations.
Use Subhan's updated importer (lon/lat retained; published PSO plan audit-only)
to obtain `data/shared_pso_250.json`, or use the reviewed shared-input snapshot
distributed with the benchmark artifact. Do not maintain two competing importers.

## Reproduce

Run from transport-algorithms, Python 3.10+ (matrix/solver standard library;
Matplotlib is needed only for experiment figures):

```powershell
python -m pip install matplotlib
python -m unittest discover -v
python build_shared_roads.py --instance data/shared_pso_250.json --provider osm --snap-to-depot-component
python audit_shared_roads.py
python research_experiments.py --instance data/shared_pso_250_road.json --stop-count-mode hard --seeds 5 --population 32 --generations 80
python map_shared_routes.py
python serve_map.py
```

The first road build makes one bounded Overpass highway query if the raw cache
is missing; an API error stops the run rather than inventing distances. Reuse
the frozen cache for exact replication. The provided measured artifact uses
the raw extract hash in RESULTS_AND_LIMITATIONS.md, bbox 18.91,47.36,19.26,47.64.
A fresh download may change OSM data and results: freeze its checksum jointly
with PSO before comparing. Do not loop requests around public-service errors.

`--snap-to-depot-component` explicitly permits audited resnapping of disconnected
nearest vertices to a nearby depot-reachable vertex. Default behavior fails.
Original addresses remain unchanged; max allowed offset defaults to 200m.
Measured offsets and limitations are recorded in the output, including the two
resnaps at customer IDs 109/237. Nearest-vertex snapping is a routing approximation,
not a verification of unloading access; offsets are not billed as road legs.

`data/shared_pso_250_road.json` contains directed distance_matrix_m and
duration_matrix_s. Both metrics describe the same time-minimizing graph path.
Payload, volumes, wages, fuel, maintenance, item data and service times are preserved.
Original source `model.not_implemented` notes are historical; active road provenance
is the `road_network` block. Static road times override the source average speeds.
The graph is common to all vehicle types; HGV-specific restrictions and turn
relations are not implemented. No real-time navigation claim.

## ORS alternative

With ORS_API_KEY set securely in your local environment:

```powershell
python build_shared_roads.py --provider ors --instance data/shared_pso_250.json --output data/shared_pso_250_road.json
```

Never place a key in code, git, screenshots or shared messages. No key was
available for the measured experiments, so live ORS is not claimed as tested.
The batched adapter is tested with directed mock matrices, caches completed
responses, and rejects null/unreachable results. Check your account's quota.
`map_shared_routes.py` specifically uses the local graph snapshot; ORS matrices
do not contain route polylines and need separate directions geometry.

## Review and data sharing

PR #5: code, tests, workflow and licensing only. Raw OSM, old data/budapest_*.json,
old Keleti maps/plots and old experiment results are removed from its diff.
PR #6: research, design, fresh small result summaries and presentation.
Generated artifacts are ignored by git, not committed through web Upload files.
The existing main-branch historical fixtures/results remain untouched.
The old blobs remain in branch history; no force push/history rewrite is needed.

The common source fleet is 2 Caddy / 2 Sprinter / 1 MAN. Idle vehicles are allowed in
the present model. Hard 10–50 stops is an explicit experiment choice, not a
claim of final agreement. Both teams must use the same road-file checksum and
constraints; the old published PSO result cannot be compared with road GA costs.
The current best main-GA plan has a 51.17-hour maximum vehicle span. Overtime
is priced, but daily/rest limits need a problem-definition decision and further work.
