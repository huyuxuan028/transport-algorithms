# Initial algorithm experiments

Budapest OSM graph / simulated delivery stops. Five seeds, population 32, 80 generations; 2432 evaluations per run. Common decoder and initial witness. Random search also uses local search. Ablations change one mechanism, but RNG trajectories also change; no statistical significance claim. Feasible means only the explicitly implemented constraints. Stop-count mode: soft

| Variant | Mean cost EUR | SD | Best | Mean seconds | Feasible |
|---|---:|---:|---:|---:|---:|
| random_search | 625.66 | 0.00 | 625.66 | 6.51 | 5/5 |
| ga | 620.29 | 1.12 | 618.34 | 5.44 | 5/5 |
| ga_unseeded | 660.08 | 3.93 | 656.11 | 6.03 | 5/5 |
| ga_no_local_search | 625.88 | 0.40 | 625.39 | 3.64 | 5/5 |
| ga_no_order_crossover | 619.62 | 1.36 | 618.52 | 5.42 | 5/5 |
