"""Optional figures for the heterogeneous development pilot; matplotlib only."""
import json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent

def main():
    pilot=json.loads((ROOT/'results/pilot.json').read_text());inst=json.loads((ROOT/'data/example.json').read_text())
    solution=json.loads((ROOT/'results/solution.json').read_text());out=ROOT/'figures';out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(9,3.2),layout='constrained')
    for objective,ax in zip(['fuel_litres','distance'],axes):
        for method,color,label in [('random','#87969E','Random + same decoder/2-opt'),('ga','#176B87','Genetic algorithm')]:
            group=[r for r in pilot['runs'] if r['method']==method and r['objective']==objective]
            xs=range(81);ys=[statistics.mean(r['history'][j]['objective'] for r in group) for j in xs]
            ax.plot(xs,ys,lw=2,color=color,label=label)
        ax.set(xlabel='Generation / evaluation batch',ylabel='Estimated fuel (L)' if objective=='fuel_litres' else 'Distance (km)',title=objective.replace('_',' '))
        ax.legend(fontsize=7);ax.grid(alpha=.15)
    fig.suptitle('Development pilot | three seeds per method, equal evaluation counts',fontsize=11)
    fig.savefig(out/'convergence.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.3),layout='constrained');palette=['#176B87','#D58820','#4B986A'];coords=inst['coordinates_km']
    for trip in solution['best']['transports']:
        path=[0]+trip['customers']+[0];k=trip['vehicle']
        ax.plot([coords[i][0] for i in path],[coords[i][1] for i in path],color=palette[k],lw=1,alpha=.7)
    ax.scatter([x[0] for x in coords[1:]],[x[1] for x in coords[1:]],s=10,c='#354653')
    ax.scatter(0,0,s=110,color='black',marker='s',label='Depot')
    for k,v in enumerate(inst['vehicles']):ax.plot([],[],color=palette[k],label=v['id'])
    ax.set(title='Fuel-objective GA | multiple sequential depot trips',xlabel='Synthetic x coordinate (km)',ylabel='Synthetic y coordinate (km)')
    ax.legend(fontsize=8);ax.grid(alpha=.1)
    fig.savefig(out/'routes.png',dpi=180);plt.close(fig)
    print('Saved figures in',out)

if __name__=='__main__':main()
