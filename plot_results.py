"""Figures and benchmark table for the heterogeneous multi-trip GA; matplotlib only.

Usage:
    python plot_results.py
    python plot_results.py --results results/solution.json --pilot results/pilot.json \
        --instance data/example.json --out figures --shift-hours 8

Produces in --out:
    dataset.png      customer map, order weight / volume / service-time histograms
    routes.png       generated witness plan vs best GA plan, one colour per vehicle
    gantt.png        trips per physical vehicle on a time axis with the shift line
    utilisation.png  payload and volume utilisation of every trip in the GA plan
    convergence.png  best objective per generation, GA vs random (from the pilot)
    BENCHMARK.md     per-run table from the pilot, written next to the figures

Every figure degrades gracefully: the optional `cost` block of a solution
(fuel/wage/overtime, added by the cost objective) is shown when present.
"""
import argparse,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
VEHICLE_COLOURS=['#176B87','#D58820','#4B986A','#A23B72','#5C5C5C']

def style():
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})

def vehicle_label(vehicles,k):
    v=vehicles[k];return f"{k}: {v.get('id',v.get('type_id','vehicle'))}"

def cost_caption(result):
    c=result.get('cost') or result.get('best',{}).get('cost')
    if not c:return ''
    return (f"  |  cost {c.get('total_eur',float('nan')):.0f} EUR"
            f" (fuel {c.get('fuel_eur',0):.0f}, wage {c.get('wage_eur',0):.0f}, maint {c.get('maintenance_eur',0):.0f};"
            f" overtime {c.get('overtime_hours',0):.1f} h)")

# ---------------------------------------------------------------- dataset
def plot_dataset(inst,out):
    customers=inst['customers'][1:];coords=inst['coordinates_km']
    fig,axes=plt.subplots(1,4,figsize=(14,3.4),layout='constrained')
    ax=axes[0];ax.scatter([x[0] for x in coords[1:]],[x[1] for x in coords[1:]],s=10,c='#354653')
    ax.scatter(0,0,s=110,color='black',marker='s',label='Depot');ax.set_aspect('equal')
    ax.set(title=f'{len(customers)} customers',xlabel='x (km)',ylabel='y (km)');ax.legend(fontsize=8);ax.grid(alpha=.1)
    for ax,key,label,colour in [(axes[1],'weight_kg','Order weight (kg)','#176B87'),
                                (axes[2],'volume_m3','Order volume (m3)','#D58820'),
                                (axes[3],'service_minutes','Service time (min)','#4B986A')]:
        values=[c[key] for c in customers]
        ax.hist(values,bins=20,color=colour,alpha=.85)
        ax.axvline(statistics.mean(values),color='black',lw=1,ls='--',label=f'mean {statistics.mean(values):.1f}')
        ax.set(xlabel=label,ylabel='orders');ax.legend(fontsize=8);ax.grid(alpha=.15)
    fig.suptitle(f"Dataset: {inst['name']}",fontsize=11)
    fig.savefig(out/'dataset.png',dpi=180);plt.close(fig)

# ----------------------------------------------------------------- routes
def draw_plan(ax,inst,trips,vehicles,title):
    coords=inst['coordinates_km']
    for trip in trips:
        path=[0]+trip['customers']+[0];k=trip['vehicle']
        ax.plot([coords[i][0] for i in path],[coords[i][1] for i in path],
                color=VEHICLE_COLOURS[k%len(VEHICLE_COLOURS)],lw=1,alpha=.75)
    ax.scatter([x[0] for x in coords[1:]],[x[1] for x in coords[1:]],s=8,c='#354653',zorder=3)
    ax.scatter(0,0,s=110,color='black',marker='s',label='Depot',zorder=4)
    for k in sorted(set(t['vehicle'] for t in trips)):
        ax.plot([],[],color=VEHICLE_COLOURS[k%len(VEHICLE_COLOURS)],label=vehicle_label(vehicles,k))
    ax.set(title=title,xlabel='x (km)',ylabel='y (km)');ax.set_aspect('equal');ax.legend(fontsize=7);ax.grid(alpha=.1)

def plot_routes(inst,result,out):
    witness=inst['reference_transports'];best=result['best']
    fig,axes=plt.subplots(1,2,figsize=(12,5.4),layout='constrained')
    wd=sum(t['distance_km'] for t in witness);wf=sum(t['fuel_litres'] for t in witness)
    draw_plan(axes[0],inst,witness,inst['vehicles'],f'Generated witness plan | {len(witness)} trips, {wd:.0f} km, {wf:.1f} L')
    draw_plan(axes[1],inst,best['transports'],best['fleet'],
              f"GA plan ({result['objective']}) | {len(best['transports'])} trips, {best['distance_km']:.0f} km, {best['fuel_litres']:.1f} L")
    fig.suptitle('Routes: one colour per physical vehicle, every trip returns to the depot'+cost_caption(result),fontsize=10)
    fig.savefig(out/'routes.png',dpi=180);plt.close(fig)

# ------------------------------------------------------------------ gantt
def draw_gantt(ax,trips,vehicles,shift_minutes,title):
    n=len(vehicles)
    for trip in trips:
        k=trip['vehicle'];start=trip['start_minutes'];dur=trip['finish_minutes']-start
        ax.barh(k,dur,left=start,height=.6,color=VEHICLE_COLOURS[k%len(VEHICLE_COLOURS)],edgecolor='white',alpha=.9)
        if dur>25:ax.text(start+dur/2,k,str(len(trip['customers'])),ha='center',va='center',fontsize=7,color='white')
    ax.axvline(shift_minutes,color='red',ls='--',lw=1.2,label=f'{shift_minutes/60:.0f} h shift')
    finish=max((t['finish_minutes'] for t in trips),default=0)
    if finish>shift_minutes:ax.axvspan(shift_minutes,finish,color='red',alpha=.06,label='overtime')
    ax.set_yticks(range(n));ax.set_yticklabels([vehicle_label(vehicles,k) for k in range(n)],fontsize=8)
    ax.invert_yaxis();ax.set(xlabel='minutes since start of day',title=title);ax.legend(fontsize=8,loc='lower right');ax.grid(axis='x',alpha=.15)

def plot_gantt(inst,result,shift_hours,out):
    shift=shift_hours*60;best=result['best']
    fig,axes=plt.subplots(2,1,figsize=(11,5.6),layout='constrained',sharex=True)
    draw_gantt(axes[0],inst['reference_transports'],inst['vehicles'],shift,'Generated witness plan (number = stops in trip)')
    draw_gantt(axes[1],best['transports'],best['fleet'],shift,f"GA plan ({result['objective']})")
    fig.suptitle('Trip schedule per physical vehicle; sequential trips, no reload delay'+cost_caption(result),fontsize=10)
    fig.savefig(out/'gantt.png',dpi=180);plt.close(fig)

# ------------------------------------------------------------ utilisation
def plot_utilisation(inst,result,out,volume_buffer=None):
    best=result['best'];c=inst['customers'];fleet=best['fleet'];trips=best['transports']
    w=[sum(c[i]['weight_kg'] for i in t['customers'])/fleet[t['vehicle']]['payload_kg']*100 for t in trips]
    v=[sum(c[i]['volume_m3'] for i in t['customers'])/fleet[t['vehicle']]['volume_m3']*100 for t in trips]
    stops=[len(t['customers']) for t in trips];colours=[VEHICLE_COLOURS[t['vehicle']%len(VEHICLE_COLOURS)] for t in trips]
    fig,axes=plt.subplots(1,2,figsize=(12,3.8),layout='constrained')
    x=range(len(trips));ax=axes[0]
    ax.bar([i-.2 for i in x],w,.4,color=colours,alpha=.9,label='payload %');ax.bar([i+.2 for i in x],v,.4,color=colours,alpha=.45,hatch='//',label='volume %')
    ax.axhline(100,color='black',lw=1)
    if volume_buffer:ax.axhline(100*(1-volume_buffer),color='red',ls='--',lw=1,label=f'volume limit with {volume_buffer:.0%} buffer')
    ax.set(xlabel='trip (colour = vehicle)',ylabel='% of capacity',title='Load utilisation per trip');ax.legend(fontsize=8);ax.grid(axis='y',alpha=.15)
    ax=axes[1];ax.bar(x,stops,color=colours)
    for y,label in [(10,'min 10'),(50,'max 50')]:ax.axhline(y,color='red',ls='--',lw=1);ax.text(len(trips)-.5,y+.5,label,ha='right',fontsize=8,color='red')
    ax.set(xlabel='trip',ylabel='stops',title='Stops per trip vs brief (10-50)');ax.grid(axis='y',alpha=.15)
    fig.savefig(out/'utilisation.png',dpi=180);plt.close(fig)

# ------------------------------------------------------------ convergence
def plot_convergence(pilot,out):
    objectives=sorted(set(r['objective'] for r in pilot['runs']))
    fig,axes=plt.subplots(1,len(objectives),figsize=(4.5*len(objectives),3.2),layout='constrained',squeeze=False)
    for objective,ax in zip(objectives,axes[0]):
        for method,color,label in [('random','#87969E','Random + same decoder/2-opt'),('ga','#176B87','Genetic algorithm')]:
            group=[r for r in pilot['runs'] if r['method']==method and r['objective']==objective]
            if not group:continue
            n=min(len(r['history']) for r in group)
            ys=[statistics.mean(r['history'][j]['objective'] for r in group) for j in range(n)]
            ax.plot(range(n),ys,lw=2,color=color,label=f'{label} (mean of {len(group)} seeds)')
        unit={'fuel_litres':'Estimated fuel (L)','distance':'Distance (km)','cost':'Cost (EUR)'}.get(objective,objective)
        ax.set(xlabel='Generation',ylabel=unit,title=objective.replace('_',' '));ax.legend(fontsize=7);ax.grid(alpha=.15)
    fig.suptitle(pilot.get('protocol','Pilot')[:90],fontsize=9)
    fig.savefig(out/'convergence.png',dpi=180);plt.close(fig)

# -------------------------------------------------------------- benchmark
def write_benchmark(pilot,out):
    rows=['# Benchmark (development pilot)','',f"Instance: `{pilot['instance']}`  ",f"Protocol: {pilot.get('protocol','')}",'',
          '| objective | method | seed | distance km | fuel L | trips | vehicles used | max finish (h) | overtime h | cost EUR | evaluations | runtime s |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in sorted(pilot['runs'],key=lambda r:(r['objective'],r['method'],r['seed'])):
        val=r['validation'];cost=r.get('cost') or r['best'].get('cost') or {}
        finish=max(val['finish_minutes_by_vehicle'])/60
        rows.append(f"| {r['objective']} | {r['method']} | {r['seed']} | {val['distance_km']:.1f} | {val['fuel_litres']:.2f} | {val['trips']} | "
                    f"{val['vehicles_used']} | {finish:.1f} | {cost.get('overtime_hours','-') if cost else '-'} | "
                    f"{cost.get('total_eur','-') if cost else '-'} | {r['evaluations']} | {r['runtime_seconds']:.2f} |")
    rows+=['','## Means per configuration','','| objective | method | runs | mean distance km | mean fuel L | best fuel L | mean runtime s |','|---|---|---|---|---|---|---|']
    for s in pilot['summary']:
        rows.append(f"| {s['objective']} | {s['method']} | {s['runs']} | {s['mean_distance_km']:.1f} | {s['mean_fuel_litres']:.2f} | {s['best_fuel_litres']:.2f} | {s['mean_runtime_seconds']:.2f} |")
    rows+=['','No certified optimum exists for this instance, so no optimality gap is reported. "overtime h" and "cost EUR" are filled once runs are produced with the cost objective.']
    (out/'BENCHMARK.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--results',type=Path,default=ROOT/'results/solution.json');p.add_argument('--pilot',type=Path,default=ROOT/'results/pilot.json')
    p.add_argument('--instance',type=Path,default=ROOT/'data/example.json');p.add_argument('--out',type=Path,default=ROOT/'figures')
    p.add_argument('--shift-hours',type=float,default=None,help='shift length for the Gantt line; default from instance model.shift_hours or 8')
    p.add_argument('--volume-buffer',type=float,default=None,help='fraction of volume kept free; default from instance model.volume_buffer')
    a=p.parse_args();style();a.out.mkdir(parents=True,exist_ok=True)
    inst=json.loads(a.instance.read_text());result=json.loads(a.results.read_text())
    shift=a.shift_hours if a.shift_hours is not None else inst['model'].get('shift_hours',8)
    buffer=a.volume_buffer if a.volume_buffer is not None else inst['model'].get('volume_buffer')
    plot_dataset(inst,a.out);plot_routes(inst,result,a.out);plot_gantt(inst,result,shift,a.out);plot_utilisation(inst,result,a.out,buffer)
    if a.pilot.exists():
        pilot=json.loads(a.pilot.read_text());plot_convergence(pilot,a.out);write_benchmark(pilot,a.out)
    else:print('no pilot file; skipping convergence.png and BENCHMARK.md')
    print('Saved figures in',a.out)

if __name__=='__main__':main()
