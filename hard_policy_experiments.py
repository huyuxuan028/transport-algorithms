"""Separate hard-stop scenario; do not mix its scores with soft-policy results."""
import json,statistics
from pathlib import Path
from solver import solve

def main():
    x=json.loads(Path('data/budapest_road.json').read_text());x['model']['stop_count_mode']='hard';x['name']+='-hard10-50';Path('data/budapest_hard.json').write_text(json.dumps(x,indent=2))
    out=Path('hard_policy_results');out.mkdir(exist_ok=True);runs=[]
    for seed in range(5):
        r=solve(x,seed=seed,population=32,generations=80,objective='cost');runs.append(r);(out/f'seed_{seed}.json').write_text(json.dumps(r,indent=2));print(seed,r['validation']['cost'],flush=True)
    values=[r['validation']['cost']['total_eur'] for r in runs]
    (out/'SUMMARY.md').write_text('# Hard 10–50 stop scenario\n\nSame Budapest OSM graph and demands; only the stop-count policy changes. Five seeds, population 32, generations 80. Hard-policy fallback initialization may use extra evaluations, recorded per run. Group assignment mutation moves at least the minimum number of customers, enabling activation of idle vehicles.\n\n| Seed | Cost EUR | Trips | Used vehicles | Below/above stop bounds | Evaluations |\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(f"| {r['seed']} | {r['validation']['cost']['total_eur']:.2f} | {r['validation']['trips']} | {r['validation']['vehicles_used']} | {r['validation']['cost']['trips_below_min']}/{r['validation']['cost']['trips_above_max']} | {r['evaluations']} |" for r in runs)+f'\n\nMean: {statistics.mean(values):.2f} EUR; sample SD: {statistics.stdev(values):.2f}. This is preliminary sensitivity evidence, not a proof of robust convergence or real operating feasibility. Unlimited horizon, no rest rules, no 3D packing or truck-access checks.\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,5))
    for r in runs:ax.plot([h['generation'] for h in r['history']],[h['objective'] for h in r['history']],label='Seed '+str(r['seed']))
    ax.set(xlabel='Generation',ylabel='Best-so-far cost EUR',title='Budapest OSM / hard stop-count scenario');ax.legend();fig.tight_layout();fig.savefig(out/'convergence.png',dpi=140)
if __name__=='__main__':main()
