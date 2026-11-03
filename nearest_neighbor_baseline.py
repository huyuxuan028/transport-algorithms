"""One-pass constructive comparison, same witness allocation and cost evaluator.
This is not a matched-budget competitor; report its single construction separately.
"""
import argparse,json,time
from pathlib import Path
from solver import decode,validate_instance,validate_solution

def main():
    p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,default=Path('data/budapest_road.json'));p.add_argument('--output',type=Path,default=Path('results/budapest_nearest_neighbor.json'));a=p.parse_args()
    x=json.loads(a.instance.read_text());validate_instance(x);start=time.perf_counter();n=len(x['customers'])-1;assignment=[None]*n
    for trip in x['reference_transports']:
        for i in trip['customers']:assignment[i-1]=trip['vehicle']
    order=[];d=x['distance_matrix_m']
    for k in range(len(x['vehicles'])):
        remaining={i for i in range(1,n+1) if assignment[i-1]==k};last=0
        while remaining:
            nxt=min(remaining,key=lambda i:(d[last][i],i));order.append(nxt);remaining.remove(nxt);last=nxt
    ids={v['id']:i for i,v in enumerate(x['vehicle_types'])};types=[ids[v['type_id']] for v in x['vehicles']]
    best=decode([order,assignment,types],x,search_objective='cost');result={'instance':x['name'],'method':'nearest_neighbor_with_witness_assignment_and_one_2opt_pass','evaluations':1,'runtime_seconds':time.perf_counter()-start,'best':best,'validation':validate_solution(x,best['transports'],best['fleet']),'note':'One-pass constructive reference. No equal-budget claim. Reference allocation is inherited, not independently optimized.'}
    a.output.parent.mkdir(exist_ok=True,parents=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result['validation']['cost']))
if __name__=='__main__':main()
