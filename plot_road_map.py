"""Static export of actual OSM geometry and road paths, without map tiles."""
import json
from pathlib import Path
from budapest_osm import graph_from_osm,shortest

def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    x=json.loads(Path('data/budapest_road.json').read_text());r=json.loads(Path('results/budapest_solution.json').read_text());raw=json.loads(Path('data/budapest_osm_raw.json').read_text());nodes,g=graph_from_osm(raw);colors=['#0072b2','#d55e00','#009e73','#cc79a7','#b28600'];fig,ax=plt.subplots(figsize=(10,8));seen=set()
    for u,edges in g.items():
        for v,_,_ in edges:
            if tuple(sorted([u,v])) in seen:continue
            seen.add(tuple(sorted([u,v])));ax.plot([nodes[u][0],nodes[v][0]],[nodes[u][1],nodes[v][1]],color='#ccd7df',lw=.7,zorder=1)
    cache={};ids=x['osm_node_ids']
    for trip in r['best']['transports']:
        order=[0]+trip['customers']+[0];path=[]
        for a,b in zip(order,order[1:]):
            u,v=ids[a],ids[b]
            if u not in cache:cache[u]=shortest(g,u)[2]
            current=v;part=[v]
            while current!=u:current=cache[u][current];part.append(current)
            path.extend(reversed(part))
        ax.plot([nodes[k][0] for k in path],[nodes[k][1] for k in path],color=colors[trip['vehicle']],lw=1.2,alpha=.65,zorder=2)
    ax.scatter([p[0] for p in x['coordinates_lonlat'][1:]],[p[1] for p in x['coordinates_lonlat'][1:]],s=4,color='#263949',zorder=3)
    depot=x['coordinates_lonlat'][0];ax.scatter(*depot,marker='*',s=170,c='black',zorder=4);ax.annotate('Simulated depot / Keleti',depot,xytext=(10,10),textcoords='offset points',fontsize=9,backgroundcolor='white')
    ax.set_aspect(1/__import__('math').cos(__import__('math').radians(depot[1])));ax.set(xlabel='Longitude',ylabel='Latitude',title='Budapest / Keleti: actual OSM road routes\n250 simulated customers · five available vehicles · soft stop-count policy')
    ax.legend(handles=[Line2D([0],[0],color=c,label='Vehicle '+str(k+1)) for k,c in enumerate(colors)],loc='upper right',fontsize=8);ax.grid(alpha=.15);fig.text(.06,.015,'Map data © OpenStreetMap contributors (ODbL) · simplified car graph; not truck navigation',fontsize=9);fig.tight_layout(rect=(0,.025,1,1));fig.savefig('Budapest_Routes.png',dpi=160)
if __name__=='__main__':main()
