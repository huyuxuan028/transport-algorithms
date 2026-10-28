"""Matched evaluation-count pilot; no claim of a shared final benchmark."""
import argparse,json,statistics,platform,sys
from pathlib import Path
from solver import solve
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--instance',type=Path,default=ROOT/'data/example.json')
    p.add_argument('--pilot-output',type=Path,default=ROOT/'results/pilot.json')
    p.add_argument('--solution-output',type=Path,default=ROOT/'results/solution.json')
    p.add_argument('--population',type=int,default=32)
    p.add_argument('--generations',type=int,default=80)
    p.add_argument('--seeds',type=int,default=3)
    p.add_argument('--best-objective',choices=['fuel_litres','distance','cost'],default='fuel_litres')
    a=p.parse_args()
    if a.seeds<1:raise ValueError('At least one seed is required')
    inst=json.loads(a.instance.read_text());runs=[];summary=[]
    for objective in ['fuel_litres','distance','cost']:
        for method in ['random','ga']:
            group=[]
            for seed in range(a.seeds):
                r=solve(inst,seed,a.population,a.generations,objective,method);runs.append(r);group.append(r)
                print(objective,method,seed,round(r['validation']['distance_km'],3),round(r['validation']['fuel_litres'],3),round(r['validation']['cost']['total_eur'],3),flush=True)
            summary.append({'objective':objective,'method':method,'runs':a.seeds,
                'mean_distance_km':statistics.mean(r['validation']['distance_km'] for r in group),
                'mean_fuel_litres':statistics.mean(r['validation']['fuel_litres'] for r in group),
                'mean_cost_eur':statistics.mean(r['validation']['cost']['total_eur'] for r in group),
                'mean_runtime_seconds':statistics.mean(r['runtime_seconds'] for r in group),
                'best_distance_km':min(r['validation']['distance_km'] for r in group),
                'best_fuel_litres':min(r['validation']['fuel_litres'] for r in group),
                'best_cost_eur':min(r['validation']['cost']['total_eur'] for r in group),
                'feasible_runs':sum(r['validation']['feasible'] for r in group)})
    evaluations=a.population*(a.generations+1)-2*a.generations
    out={'instance':inst['name'],'protocol':f'{6*a.seeds} runs, seeds 0..{a.seeds-1}, population {a.population}, generations {a.generations}, {evaluations} candidate evaluations per run. GA and random search share the same decoder and bounded 2-opt. Not equal wall-clock budgets.',
        'environment':{'python':sys.version,'platform':platform.platform()},'summary':summary,'runs':runs}
    a.pilot_output.parent.mkdir(parents=True,exist_ok=True)
    a.solution_output.parent.mkdir(parents=True,exist_ok=True)
    a.pilot_output.write_text(json.dumps(out,indent=2,allow_nan=False))
    score=lambda r: r['validation']['cost']['total_eur'] if a.best_objective=='cost' else (
        r['validation']['distance_km'] if a.best_objective=='distance' else r['validation']['fuel_litres'])
    best=min((r for r in runs if r['method']=='ga' and r['objective']==a.best_objective),key=score)
    a.solution_output.write_text(json.dumps(best,indent=2,allow_nan=False))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()

