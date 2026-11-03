# Benchmark (development pilot)

Instance: `Heterogeneous-102-five-vehicle-seed42`  
Protocol: 18 runs, seeds 0..2, population 32, generations 80, 2432 candidate evaluations per run. GA and random search share the same decoder and bounded 2-opt. Not equal wall-clock budgets.

| objective | method | seed | distance km | fuel L | trips | vehicles used | max finish (h) | overtime h | cost EUR | evaluations | runtime s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cost | ga | 0 | 855.9 | 85.92 | 10 | 5 | 9.6 | 2.4045 | 754.3099 | 2432 | 1.18 |
| cost | ga | 1 | 876.1 | 100.23 | 12 | 5 | 8.7 | 1.5357 | 785.7901 | 2432 | 1.17 |
| cost | ga | 2 | 846.0 | 88.88 | 12 | 5 | 9.5 | 2.5982 | 760.6031 | 2432 | 1.12 |
| cost | random | 0 | 1575.9 | 119.20 | 25 | 5 | 14.1 | 21.5138 | 1341.6474 | 2432 | 1.36 |
| cost | random | 1 | 1587.0 | 129.92 | 21 | 5 | 16.2 | 22.048 | 1378.0421 | 2432 | 1.31 |
| cost | random | 2 | 1572.8 | 142.29 | 16 | 5 | 18.6 | 21.4227 | 1394.8124 | 2432 | 1.24 |
| distance | ga | 0 | 758.8 | 147.10 | 5 | 5 | 9.6 | 2.3302 | 851.1735 | 2432 | 1.50 |
| distance | ga | 1 | 682.6 | 142.60 | 5 | 5 | 9.2 | 1.1667 | 796.9186 | 2432 | 1.43 |
| distance | ga | 2 | 753.2 | 157.34 | 5 | 5 | 9.9 | 2.1153 | 868.8109 | 2432 | 1.47 |
| distance | random | 0 | 1504.2 | 192.88 | 15 | 5 | 14.3 | 19.4637 | 1452.0865 | 2432 | 1.30 |
| distance | random | 1 | 1540.9 | 155.18 | 19 | 5 | 17.0 | 20.9395 | 1402.2181 | 2432 | 1.31 |
| distance | random | 2 | 1516.9 | 257.51 | 11 | 5 | 18.0 | 21.1019 | 1621.1249 | 2432 | 1.30 |
| fuel_litres | ga | 0 | 1386.5 | 83.94 | 34 | 5 | 12.4 | 16.1005 | 1119.9271 | 2432 | 0.86 |
| fuel_litres | ga | 1 | 1324.2 | 81.91 | 34 | 5 | 13.1 | 15.8816 | 1088.7532 | 2432 | 0.89 |
| fuel_litres | ga | 2 | 1309.2 | 81.54 | 33 | 5 | 14.0 | 15.3039 | 1075.2026 | 2432 | 0.93 |
| fuel_litres | random | 0 | 1726.4 | 109.78 | 34 | 5 | 18.7 | 25.8121 | 1427.7865 | 2432 | 1.29 |
| fuel_litres | random | 1 | 1845.0 | 112.09 | 38 | 5 | 16.0 | 29.2024 | 1519.1575 | 2432 | 1.35 |
| fuel_litres | random | 2 | 1844.7 | 112.75 | 36 | 5 | 15.6 | 29.1932 | 1520.5022 | 2432 | 1.30 |

## Means per configuration

| objective | method | runs | mean distance km | mean fuel L | best fuel L | mean runtime s |
|---|---|---|---|---|---|---|
| fuel_litres | random | 3 | 1805.4 | 111.54 | 109.78 | 1.31 |
| fuel_litres | ga | 3 | 1340.0 | 82.46 | 81.54 | 0.89 |
| distance | random | 3 | 1520.7 | 201.86 | 155.18 | 1.31 |
| distance | ga | 3 | 731.6 | 149.01 | 142.60 | 1.47 |
| cost | random | 3 | 1578.6 | 130.47 | 119.20 | 1.30 |
| cost | ga | 3 | 859.3 | 91.68 | 85.92 | 1.16 |

No certified optimum exists for this instance, so no optimality gap is reported. "overtime h" and "cost EUR" are filled once runs are produced with the cost objective.
