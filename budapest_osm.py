"""Shared-instance OSM street graph utilities. No customer locations are generated.
Simplified motorcar graph; turn relations and HGV restrictions are not modeled.
"""
import argparse,copy,datetime,hashlib,heapq,json,math,random,re,urllib.parse,urllib.request
from pathlib import Path
from solver import schedule
CLASSES={'motorway':60,'motorway_link':40,'trunk':50,'trunk_link':40,'primary':40,'primary_link':30,'secondary':35,'secondary_link':30,'tertiary':30,'tertiary_link':25,'residential':25,'unclassified':25,'living_street':15,'service':15}

def metres(a,b):
    lat1,lat2=map(math.radians,[a[1],b[1]]);dl=math.radians(b[0]-a[0]);dp=lat2-lat1
    h=math.sin(dp/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dl/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(h)))

def graph_from_osm(data):
    nodes={e['id']:[e['lon'],e['lat']] for e in data['elements'] if e['type']=='node'};graph={}
    for e in data['elements']:
        if e['type']!='way':continue
        t=e.get('tags',{});kind=t.get('highway');access=next((t[k] for k in ['motorcar','motor_vehicle','vehicle','access'] if k in t),'yes')
        if kind not in CLASSES or access in ['no','private','agricultural','forestry'] or t.get('area')=='yes':continue
        speed=CLASSES[kind];tag=t.get('maxspeed','');m=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(mph)?',tag)
        if m:speed=min(speed,float(m[1])*(1.609344 if m[2] else 1))
        if speed<=0:continue
        direction=t.get('oneway', 'yes' if t.get('junction')=='roundabout' or kind=='motorway' else 'no')
        for u,v in zip(e['nodes'],e['nodes'][1:]):
            if u not in nodes or v not in nodes:continue
            dist=metres(nodes[u],nodes[v]);secs=dist/speed*3.6
            graph.setdefault(u,[]);graph.setdefault(v,[])
            if direction not in ['-1','reverse']:graph[u].append((v,dist,secs))
            if direction not in ['yes','1','true']:graph[v].append((u,dist,secs))
    return nodes,graph

def component(graph,root):
    def reach(g):
        seen={root};stack=[root]
        while stack:
            for nxt in g.get(stack.pop(),[]):
                if nxt not in seen:seen.add(nxt);stack.append(nxt)
        return seen
    forward={u:[e[0] for e in es] for u,es in graph.items()};reverse={u:[] for u in graph}
    for u,vs in forward.items():
        for v in vs:reverse[v].append(u)
    return reach(forward)&reach(reverse)

def shortest(graph,source):
    time={source:0.};distance={source:0.};parent={};queue=[(0.,source)]
    while queue:
        elapsed,u=heapq.heappop(queue)
        if elapsed!=time[u]:continue
        for v,d,t in graph[u]:
            value=elapsed+t
            if value<time.get(v,math.inf):
                time[v]=value;distance[v]=distance[u]+d;parent[v]=u;heapq.heappush(queue,(value,v))
    return distance,time,parent
