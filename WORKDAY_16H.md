# Budapest shared 16-hour benchmark

Use the frozen `data/shared_pso_250_road.json` attachment with SHA-256
`6d794dff4a03cebb1f9127796209fa1f263450a780ce76ade9c26244b6a2676c`.
The file contains the depot, 250 Budapest customer addresses and directed road
distance and duration matrices. The source attachment and its map audit remain
the provenance for this benchmark.

## Workday and cost

Set `model.time_horizon_minutes` to `960`. Time zero is 08:00 local. Each active
vehicle starts at minute zero and returns to the depot after every trip. Count
directed road travel, including depot legs, and all customer service
(`service_minutes` includes loading and unloading). A final return at minute
960 is valid. Idle vehicles record zero minutes. Regular wages cover the first
480 minutes and overtime uses double the regular rate. The shared fleet,
capacity reserve and stop penalties come from the source model.

## Full 250-address run

The run uses GA seed 0, cost objective, population 32 and 200 generations.
The saved result is `results/shared_pso_250_road_workday_16h.json`. Independent
validation confirmed the result after 6,033 candidate evaluations. The best
plan was found during initialization and retained through generation 200.

| Vehicle | Working minutes | Depot return, local |
|---|---:|---:|
| caddy-1 | 957.82 | 23:57:49 |
| caddy-2 | 951.97 | 23:51:58 |
| sprinter-3 | 892.39 | 22:52:23 |
| sprinter-4 | 958.16 | 23:58:10 |
| man_tgl-5 | 958.78 | 23:58:47 |

Operational cost was EUR 1,860.5025. Nineteen trips incurred soft minimum-stop
penalties totaling EUR 250,000. The resulting optimization score was
EUR 251,860.5025.

To reproduce the run in PowerShell, write to a new filename:

```powershell
@'
import hashlib
import json
from pathlib import Path

from build_workday_suite import HORIZON_MINUTES, SOURCE_SHA256
from solver import solve

raw = Path('data/shared_pso_250_road.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256
instance = json.loads(raw)
instance['model']['time_horizon_minutes'] = HORIZON_MINUTES
result = solve(instance, seed=0, population=32, generations=200, objective='cost')
result.update(source_sha256=SOURCE_SHA256, time_horizon_minutes=HORIZON_MINUTES, workday_start_local='08:00')
Path('generated').mkdir(exist_ok=True)
with Path('generated/ga_250_workday_reproduction.json').open('x', encoding='utf-8') as output:
    json.dump(result, output, indent=2, allow_nan=False)
'@ | python -
```

## Shared 100-case suite

```powershell
python build_workday_suite.py
python solver.py --instance generated/shared_workday_16h/budapest-workday-16h-v1-000.json --require-road --objective cost --seed 0 --population 32 --generations 200 --output generated/ga_workday_case_000.json
```

The generator writes 100 standalone JSON files and a manifest to
`generated/shared_workday_16h`. To regenerate, pass `--output` with a new
directory. Compare the result with
`data/shared_workday_16h_manifest.json` before sharing the files between teams.
Both algorithms should read the same case files and identify each case by its
file SHA-256. Instance seeds 0–99 specify address subsets of size 150–249. Use
separate search seeds for algorithm runs.

Each case keeps the depot, source addresses, orders, fixed fleet and road
travel values. The local customer IDs index both directed matrix axes.
`source_customer_ids[local_id]` gives the original customer ID. The
`reference_transports` are filtered from the source initialization routes
and provide a common starting point. They can exceed the workday horizon,
so validate each algorithm's returned plan under `model.time_horizon_minutes`.
Feasibility was checked on all 100 cases by filtering the full run's routes
to each case and revalidating the resulting schedules. These checks establish
feasibility independently of fresh GA or PSO runs on the individual cases.
The cases share a parent road network and customer pool, so results across cases
are correlated.
