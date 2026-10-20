"""Matched evaluation-count pilot; no claim of a shared final benchmark."""
import json,statistics,platform,sys
from pathlib import Path
from solver import solve
ROOT=Path(__file__).resolve().parent

def main():
    inst=json.loads((ROOT/'data/example.json').read_text());runs=[];summary=[]
    for objective in ['fuel_litres','distance']:
        for method in ['random','ga']:
            group=[]
            for seed in range(3):
                r=solve(inst,seed,32,80,objective,method);runs.append(r);group.append(r)
                print(objective,method,seed,round(r['validation']['distance_km'],3),round(r['validation']['fuel_litres'],3),flush=True)
            summary.append({'objective':objective,'method':method,'runs':3,
                'mean_distance_km':statistics.mean(r['validation']['distance_km'] for r in group),
                'mean_fuel_litres':statistics.mean(r['validation']['fuel_litres'] for r in group),
                'mean_runtime_seconds':statistics.mean(r['runtime_seconds'] for r in group),
                'best_distance_km':min(r['validation']['distance_km'] for r in group),
                'best_fuel_litres':min(r['validation']['fuel_litres'] for r in group),
                'feasible_runs':sum(r['validation']['feasible'] for r in group)})
    folder=ROOT/'results';folder.mkdir(exist_ok=True)
    out={'instance':inst['name'],'protocol':'12 runs, seeds 0..2, population 32, generations 80, 2432 candidate evaluations per run. GA and random search share the same decoder and bounded 2-opt. Not equal wall-clock budgets.',
        'environment':{'python':sys.version,'platform':platform.platform()},'summary':summary,'runs':runs}
    (folder/'pilot.json').write_text(json.dumps(out,indent=2,allow_nan=False))
    best=min((r for r in runs if r['method']=='ga' and r['objective']=='fuel_litres'),key=lambda r:r['validation']['fuel_litres'])
    (folder/'solution.json').write_text(json.dumps(best,indent=2,allow_nan=False))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
