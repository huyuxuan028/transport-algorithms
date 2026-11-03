# GA algorithm and Budapest road-network upgrade

Candidate code and evidence for team review. Not merged into GitHub. Start with ../README.md and ../transport-findings/REQUIREMENTS_AND_READINESS.md. Resolve the existing PR #4 conflict collaboratively before uploading replacements.

## Already generated
- Budapest_Road_Map.html: real OSM street-map layers (internet) plus an offline SVG graph map. Existing 250 furniture orders are unchanged; the customer locations and depot are simulated on actual OSM nodes near Keleti.
- data/budapest_source.osm and budapest_osm_raw.json: actual downloaded graph source, ODbL. See OSM_DATA_LICENSE.md.
- data/budapest_road.json: directed distance/time matrices from the same graph paths. Local routing, NOT an ORS response.
- results/budapest_solution.json: initial soft-stop GA road solution.
- budapest_experiments/: original unseeded road experiments.
- seeded_budapest_experiments/: revised seeded GA, unseeded ablation, random and operator ablations.
- hard_policy_results/: separate hard 10–50 policy experiments. They may still have long schedules; overtime payment does not model rest periods.

## Run (Python 3.10+)
```sh
python -m pip install matplotlib
python -m unittest -v test_solver test_plot_results test_roads test_upgrade test_budapest_integration
python solver.py --instance data/budapest_road.json --require-road --objective cost --output results/my_road_solution.json
python map_budapest.py --solution results/my_road_solution.json --output My_Budapest_Map.html
python research_experiments.py --instance data/budapest_road.json --output my_experiments
python hard_policy_experiments.py
```
Map rendering is linked to the raw graph hash and independently validates the route plan. User-defined output filenames avoid overwriting the supplied experiment evidence. Cached OSM data makes solving and offline graph viewing reproducible without further API calls. To regenerate the same seeded scenario from the cached graph: python budapest_osm.py. Delete the raw file only if a fresh source is intentionally required; OSM changes can change results.

## Stops and initial population
Default stop_count_mode is soft for compatibility with the previous shared brief. --stop-count-mode hard activates both min and max in Split and the independent validator. Initialization may need a conservative single-compatible-vehicle fallback, counted as an extra evaluation. Failing to find an initial hard-feasible plan is NOT an infeasibility certificate. Group reassignment can activate idle vehicles under the hard minimum. The model still permits unused fleet slots.

The revised default adds a nearest-neighbor candidate to the initial population. Both GA and random-search comparisons get this same candidate. heuristic_seed=False is used for the GA-unseeded ablation. It is important to compare against the one-pass nearest-neighbor baseline itself: a seeded final value alone does not demonstrate useful evolutionary improvement.

## ORS option
The official service moved to https://api.heigit.org/openrouteservice/v2/ (see https://ask.openrouteservice.org/t/deprecating-api-openrouteservice-org-in-favour-of-api-heigit-org/7912). Set ORS_API_KEY locally; do not commit it or send it in chat. A key is not needed for the already-generated local OSM graph scenario.
```powershell
$env:ORS_API_KEY = "YOUR_LOCAL_KEY"
python road_network.py --instance data/benchmark_250.json --coordinates shared_coordinates_lonlat.json --output data/shared_ors.json
python solver.py --instance data/shared_ors.json --require-road --objective cost --output results/ors_solution.json
python map_routes.py --instance data/shared_ors.json --solution results/ors_solution.json --output ORS_Routes.html
```
Locations are [longitude,latitude], depot first, one entry per customer in ID order. The 25x25 batch adapter caches responses, rejects unreachable cells and preserves directed times in seconds and distances in metres. Check current account quotas. A common profile is not vehicle-specific HGV clearance verification. Live ORS execution has not been verified here. Use the same provider and matrices for both teams.

## Scope and sources
Read RESEARCH_AND_ALGORITHM.md and ../transport-findings/DESIGN_DECISIONS.md. This is not a reproduction of HGS or a novel algorithm. Finance input prices are scenario assumptions. Missing realistic restrictions must be resolved through the shared contract before claiming completion. Existing research_results/ and results/pilot.json files are legacy Euclidean experiments/test fixtures, not Budapest road results.
