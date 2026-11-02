# Benchmark (development pilot)

Instance: `Heterogeneous-250-five-vehicle-seed42`  
Protocol: 18 runs on Heterogeneous-250-five-vehicle-seed42, seeds 0..2, population 32, generations 80, 2432 candidate evaluations per run. GA and random search share the same decoder and bounded 2-opt. Not equal wall-clock budgets.

| objective | method | seed | distance km | fuel L | trips | vehicles used | max finish (h) | overtime h | cost EUR | evaluations | runtime s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cost | ga | 0 | 1935.1 | 251.42 | 27 | 5 | 23.9 | 57.0026 | 2505.5084 | 2432 | 2.62 |
| cost | ga | 1 | 1944.8 | 236.51 | 29 | 5 | 26.9 | 57.281 | 2480.4332 | 2432 | 2.70 |
| cost | ga | 2 | 2117.3 | 245.89 | 34 | 5 | 25.0 | 62.2087 | 2626.9741 | 2432 | 2.60 |
| cost | random | 0 | 3829.3 | 466.61 | 59 | 5 | 35.8 | 111.1242 | 4379.3244 | 2432 | 2.78 |
| cost | random | 1 | 3676.8 | 494.99 | 45 | 5 | 35.6 | 106.7666 | 4330.8622 | 2432 | 2.79 |
| cost | random | 2 | 3688.5 | 480.70 | 48 | 5 | 36.7 | 107.1005 | 4307.0148 | 2432 | 2.77 |
| distance | ga | 0 | 1855.7 | 234.91 | 26 | 5 | 20.5 | 54.7355 | 2410.4262 | 2432 | 2.48 |
| distance | ga | 1 | 1972.3 | 244.83 | 28 | 5 | 23.9 | 58.0665 | 2518.9878 | 2432 | 2.43 |
| distance | ga | 2 | 2119.6 | 246.24 | 39 | 5 | 24.1 | 62.2744 | 2629.3441 | 2432 | 2.41 |
| distance | random | 0 | 3740.1 | 497.43 | 44 | 5 | 39.9 | 108.5734 | 4383.5286 | 2432 | 2.71 |
| distance | random | 1 | 3676.8 | 494.99 | 45 | 5 | 35.6 | 106.7666 | 4330.8622 | 2432 | 2.68 |
| distance | random | 2 | 3688.5 | 480.70 | 48 | 5 | 36.7 | 107.1005 | 4307.0148 | 2432 | 2.69 |
| fuel_litres | ga | 0 | 2683.6 | 257.01 | 58 | 5 | 37.2 | 78.3891 | 3070.1452 | 2432 | 2.75 |
| fuel_litres | ga | 1 | 2499.8 | 251.64 | 48 | 5 | 33.5 | 73.1369 | 2921.6107 | 2432 | 2.24 |
| fuel_litres | ga | 2 | 2331.8 | 258.75 | 45 | 5 | 28.1 | 68.3367 | 2813.3908 | 2432 | 2.27 |
| fuel_litres | random | 0 | 4171.3 | 462.74 | 65 | 5 | 49.2 | 120.8943 | 4620.4411 | 2432 | 2.82 |
| fuel_litres | random | 1 | 4004.8 | 458.43 | 60 | 5 | 39.1 | 116.1374 | 4489.7395 | 2432 | 2.89 |
| fuel_litres | random | 2 | 3803.8 | 448.10 | 57 | 5 | 36.3 | 110.3951 | 4318.4256 | 2432 | 2.73 |

## Means per configuration

| objective | method | runs | mean distance km | mean fuel L | best fuel L | mean runtime s |
|---|---|---|---|---|---|---|
| fuel_litres | random | 3 | 3993.3 | 456.42 | 448.10 | 2.81 |
| fuel_litres | ga | 3 | 2505.1 | 255.80 | 251.64 | 2.42 |
| distance | random | 3 | 3701.8 | 491.04 | 480.70 | 2.69 |
| distance | ga | 3 | 1982.5 | 241.99 | 234.91 | 2.44 |
| cost | random | 3 | 3731.6 | 480.77 | 466.61 | 2.78 |
| cost | ga | 3 | 1999.1 | 244.61 | 236.51 | 2.64 |

No certified optimum exists for this instance, so no optimality gap is reported. "overtime h" and "cost EUR" are filled once runs are produced with the cost objective.
