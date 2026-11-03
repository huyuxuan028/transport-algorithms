import json,tempfile,unittest
from pathlib import Path
from solver import schedule
from test_solver import ready

try:
    import matplotlib  # noqa: F401
    import plot_results
except ImportError:  # matplotlib is an optional dependency
    plot_results=None

ROOT=Path(__file__).parent

@unittest.skipIf(plot_results is None,'matplotlib not installed')
class PlotTests(unittest.TestCase):
    def test_all_figures_and_benchmark_are_written_from_repository_results(self):
        inst=json.loads((ROOT/'data/benchmark_250.json').read_text());result=json.loads((ROOT/'results/solution.json').read_text())
        pilot=json.loads((ROOT/'results/pilot.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);plot_results.style()
            plot_results.plot_dataset(inst,out);plot_results.plot_routes(inst,result,out)
            plot_results.plot_gantt(inst,result,8,out);plot_results.plot_utilisation(inst,result,out,0.1)
            plot_results.plot_convergence(pilot,out);plot_results.write_benchmark(pilot,out)
            for name in ['dataset.png','routes.png','gantt.png','utilisation.png','convergence.png','BENCHMARK.md']:
                self.assertTrue((out/name).exists(),name);self.assertGreater((out/name).stat().st_size,0,name)
            self.assertIn('| fuel_litres | ga | 0 |',(out/'BENCHMARK.md').read_text())
    def test_gantt_and_utilisation_work_without_cost_block_on_tiny_instance(self):
        x=ready();x['coordinates_km']=[[0,0],[1,1],[2,0],[1,-1],[-1,0]];x['name']='tiny'
        x['reference_transports']=schedule([[[1,2],[3,4]],[],[],[],[]],x)
        result={'objective':'distance','best':{'fleet':x['vehicles'],'transports':x['reference_transports'],'distance_km':1,'fuel_litres':1}}
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);plot_results.style()
            plot_results.plot_gantt(x,result,8,out);plot_results.plot_utilisation(x,result,out);plot_results.plot_routes(x,result,out)
            self.assertEqual(plot_results.cost_caption(result),'')
            self.assertTrue((out/'gantt.png').exists())

if __name__=='__main__':unittest.main()
