# Benchmark (development pilot)

Instance: `Heterogeneous-102-five-vehicle-seed42`  
Protocol: 18 runs, seeds 0..2, population 32, generations 80, 2432 candidate evaluations per run. GA and random search share the same decoder and bounded 2-opt. Not equal wall-clock budgets.

| objective | method | seed | distance km | fuel L | trips | vehicles used | max finish (h) | overtime h | cost EUR | evaluations | runtime s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cost | ga | 0 | 851.3 | 96.16 | 9 | 5 | 9.4 | 1.9946 | 1089.3254 | 2432 | 0.98 |
| cost | ga | 1 | 828.3 | 93.50 | 10 | 5 | 8.3 | 0.7353 | 1044.579 | 2432 | 1.06 |
| cost | ga | 2 | 834.1 | 92.30 | 11 | 5 | 11.7 | 3.7113 | 1105.2984 | 2432 | 0.94 |
| cost | random | 0 | 1450.0 | 167.55 | 12 | 5 | 13.2 | 17.9163 | 1921.3967 | 2432 | 1.11 |
| cost | random | 1 | 1532.4 | 141.50 | 20 | 5 | 14.5 | 20.2688 | 1956.5187 | 2432 | 1.05 |
| cost | random | 2 | 1441.8 | 130.44 | 16 | 5 | 17.7 | 17.6811 | 1837.8185 | 2432 | 1.00 |
| distance | ga | 0 | 729.6 | 152.41 | 5 | 5 | 9.0 | 1.6924 | 1119.5446 | 2432 | 1.14 |
| distance | ga | 1 | 725.3 | 151.50 | 5 | 5 | 8.7 | 1.1634 | 1104.4573 | 2432 | 1.17 |
| distance | ga | 2 | 732.9 | 153.10 | 5 | 5 | 9.1 | 1.1313 | 1111.761 | 2432 | 1.13 |
| distance | random | 0 | 1450.0 | 167.55 | 12 | 5 | 13.2 | 17.9163 | 1921.3967 | 2432 | 1.13 |
| distance | random | 1 | 1500.2 | 185.24 | 15 | 5 | 16.8 | 19.6063 | 2016.8573 | 2432 | 1.05 |
| distance | random | 2 | 1441.8 | 130.44 | 16 | 5 | 17.7 | 17.6811 | 1837.8185 | 2432 | 1.06 |
| fuel_litres | ga | 0 | 1361.8 | 81.86 | 34 | 5 | 14.6 | 17.0321 | 1659.3913 | 2432 | 0.72 |
| fuel_litres | ga | 1 | 1329.8 | 81.88 | 32 | 5 | 14.9 | 17.7087 | 1654.4527 | 2432 | 0.74 |
| fuel_litres | ga | 2 | 1243.4 | 76.34 | 30 | 5 | 12.7 | 14.9587 | 1535.8084 | 2432 | 0.74 |
| fuel_litres | random | 0 | 1735.7 | 107.27 | 33 | 5 | 16.4 | 26.0793 | 2119.0888 | 2432 | 0.99 |
| fuel_litres | random | 1 | 1736.6 | 106.44 | 36 | 5 | 17.5 | 26.5981 | 2127.9216 | 2432 | 1.01 |
| fuel_litres | random | 2 | 1662.3 | 103.69 | 33 | 5 | 16.8 | 23.9822 | 2025.8719 | 2432 | 1.07 |

## Means per configuration

| objective | method | runs | mean distance km | mean fuel L | best fuel L | mean runtime s |
|---|---|---|---|---|---|---|
| fuel_litres | random | 3 | 1711.6 | 105.80 | 103.69 | 1.03 |
| fuel_litres | ga | 3 | 1311.7 | 80.03 | 76.34 | 0.73 |
| distance | random | 3 | 1464.0 | 161.08 | 130.44 | 1.08 |
| distance | ga | 3 | 729.3 | 152.34 | 151.50 | 1.15 |
| cost | random | 3 | 1474.7 | 146.50 | 130.44 | 1.05 |
| cost | ga | 3 | 837.9 | 93.99 | 92.30 | 1.00 |

No certified optimum exists for this instance, so no optimality gap is reported. "overtime h" and "cost EUR" are filled once runs are produced with the cost objective.
