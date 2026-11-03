"""Reproducible multi-seed ablations on one explicitly identified shared matrix."""
import argparse,hashlib,json,statistics,platform,sys
from pathlib import Path
from solver import solve

def main():
    p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,default=Path('data/shared_pso_250_road.json'));p.add_argument('--output',type=Path,default=Path('generated/shared_experiments'));p.add_argument('--seeds',type=int,default=5);p.add_argument('--population',type=int,default=32);p.add_argument('--generations',type=int,default=80);p.add_argument('--stop-count-mode',choices=['hard','soft'],default='hard');a=p.parse_args()
    if a.seeds<1: p.error('--seeds must be positive')
    x=json.loads(a.instance.read_text());x['model']['stop_count_mode']=a.stop_count_mode;runs=[]
    road=x.get('road_network',{});label=('Shared Budapest addresses / local OSM graph' if road.get('provider')=='local_osm_dijkstra' else 'ORS road matrix' if road else 'Shared source matrix / non-road distances')
    variants=[('random_search',{'method':'random'}),('ga',{}),('ga_unseeded',{'heuristic_seed':False}),('ga_no_local_search',{'local_search':False}),('ga_no_order_crossover',{'crossover_rate':0.0})]
    for name,kwargs in variants:
        for seed in range(a.seeds):
            r=solve(x,seed=seed,population=a.population,generations=a.generations,objective='cost',**kwargs);r['variant']=name;runs.append(r)
            print(name,seed,r['validation']['cost']['total_eur'],flush=True)
    a.output.mkdir(exist_ok=True,parents=True)
    for r in runs:
        if r['variant']=='ga':(a.output/('ga_seed_'+str(r['seed'])+'.json')).write_text(json.dumps(r,indent=2))
    (a.output/'runs.json').write_text(json.dumps({'instance':x['name'],'instance_sha256':hashlib.sha256(a.instance.read_bytes()).hexdigest(),'road_network':road,'stop_count_mode':a.stop_count_mode,'population':a.population,'generations':a.generations,'seeds':a.seeds,'python':sys.version,'platform':platform.platform(),'runs':runs},indent=2))
    lines=['# Initial algorithm experiments','',label+f'. {a.seeds} seeds, population {a.population}, {a.generations} generations. Actual candidate evaluations are recorded per run; hard-mode fallback construction can add evaluations. Common decoder and initial witness. Random search also uses local search. Ablations change one mechanism, but RNG trajectories also change; no statistical significance claim. Feasible means only the explicitly implemented constraints. Stop-count mode: '+x['model'].get('stop_count_mode','soft'),'','| Variant | Mean cost EUR | SD | Best | Mean seconds | Feasible |','|---|---:|---:|---:|---:|---:|']
    for name,_ in variants:
        group=[r for r in runs if r['variant']==name];vals=[r['validation']['cost']['total_eur'] for r in group]
        lines.append(f'| {name} | {statistics.mean(vals):.2f} | {(statistics.stdev(vals) if len(vals)>1 else 0.0):.2f} | {min(vals):.2f} | {statistics.mean(r["runtime_seconds"] for r in group):.2f} | {sum(r["validation"]["feasible"] for r in group)}/{a.seeds} |')
    best=min((r for r in runs if r['variant']=='ga'),key=lambda r:r['validation']['cost']['total_eur'])
    (a.output/'best_solution.json').write_text(json.dumps(best,indent=2,allow_nan=False))
    (a.output/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,5))
    for name,_ in variants:
        group=[r for r in runs if r['variant']==name]
        means=[statistics.mean(r['history'][i]['objective'] for r in group) for i in range(a.generations+1)]
        ax.plot(range(a.generations+1),means,label=name)
        ax.fill_between(range(a.generations+1),[min(r['history'][i]['objective'] for r in group) for i in range(a.generations+1)],[max(r['history'][i]['objective'] for r in group) for i in range(a.generations+1)],alpha=.12)
    ax.set(xlabel='Generation',ylabel='Mean best-so-far cost (EUR)',title='Algorithm behavior: '+label);ax.legend();fig.tight_layout();fig.savefig(a.output/'convergence.png',dpi=150)
if __name__=='__main__':main()
