"""Matched-budget ablations on the current shared-input snapshot, not an ORS run."""
import argparse,hashlib,json,statistics,platform,sys
from pathlib import Path
from solver import solve

def main():
    p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,default=Path('data/benchmark_250.json'));p.add_argument('--output',type=Path,default=Path('research_results'));a=p.parse_args()
    x=json.loads(a.instance.read_text());runs=[]
    road=x.get('road_network',{});label=('Budapest OSM graph / simulated delivery stops' if road.get('provider')=='local_osm_dijkstra' else 'ORS road matrix' if road else 'Synthetic coordinates / Euclidean distances')
    variants=[('random_search',{'method':'random'}),('ga',{}),('ga_unseeded',{'heuristic_seed':False}),('ga_no_local_search',{'local_search':False}),('ga_no_order_crossover',{'crossover_rate':0.0})]
    for name,kwargs in variants:
        for seed in range(5):
            r=solve(x,seed=seed,population=32,generations=80,objective='cost',**kwargs);r['variant']=name;runs.append(r)
            print(name,seed,r['validation']['cost']['total_eur'],flush=True)
    a.output.mkdir(exist_ok=True,parents=True)
    for r in runs:
        if r['variant']=='ga':(a.output/('ga_seed_'+str(r['seed'])+'.json')).write_text(json.dumps(r,indent=2))
    (a.output/'runs.json').write_text(json.dumps({'instance':x['name'],'instance_sha256':hashlib.sha256(a.instance.read_bytes()).hexdigest(),'road_network':road,'python':sys.version,'platform':platform.platform(),'runs':runs},indent=2))
    lines=['# Initial algorithm experiments','',label+'. Five seeds, population 32, 80 generations; 2432 evaluations per run. Common decoder and initial witness. Random search also uses local search. Ablations change one mechanism, but RNG trajectories also change; no statistical significance claim. Feasible means only the explicitly implemented constraints. Stop-count mode: '+x['model'].get('stop_count_mode','soft'),'','| Variant | Mean cost EUR | SD | Best | Mean seconds | Feasible |','|---|---:|---:|---:|---:|---:|']
    for name,_ in variants:
        group=[r for r in runs if r['variant']==name];vals=[r['validation']['cost']['total_eur'] for r in group]
        lines.append(f'| {name} | {statistics.mean(vals):.2f} | {statistics.stdev(vals):.2f} | {min(vals):.2f} | {statistics.mean(r["runtime_seconds"] for r in group):.2f} | {sum(r["validation"]["feasible"] for r in group)}/5 |')
    (a.output/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,5))
    for name,_ in variants:
        group=[r for r in runs if r['variant']==name]
        means=[statistics.mean(r['history'][i]['objective'] for r in group) for i in range(81)]
        ax.plot(range(81),means,label=name)
        ax.fill_between(range(81),[min(r['history'][i]['objective'] for r in group) for i in range(81)],[max(r['history'][i]['objective'] for r in group) for i in range(81)],alpha=.12)
    ax.set(xlabel='Generation',ylabel='Mean best-so-far cost (EUR)',title='Five-seed algorithm behavior: '+label);ax.legend();fig.tight_layout();fig.savefig(a.output/'convergence.png',dpi=150)
if __name__=='__main__':main()
