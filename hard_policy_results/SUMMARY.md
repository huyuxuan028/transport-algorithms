# Hard 10–50 stop scenario

Same Budapest OSM graph and demands; only the stop-count policy changes. Five seeds, population 32, generations 80. Hard-policy fallback initialization may use extra evaluations, recorded per run. Group assignment mutation moves at least the minimum number of customers, enabling activation of idle vehicles.

| Seed | Cost EUR | Trips | Used vehicles | Below/above stop bounds | Evaluations |
|---|---:|---:|---:|---:|---:|
| 0 | 883.29 | 16 | 4 | 0/0 | 2433 |
| 1 | 871.52 | 17 | 4 | 0/0 | 2433 |
| 2 | 895.91 | 16 | 4 | 0/0 | 2433 |
| 3 | 836.54 | 17 | 4 | 0/0 | 2433 |
| 4 | 863.20 | 17 | 3 | 0/0 | 2433 |

Mean: 870.09 EUR; sample SD: 22.45. This is preliminary sensitivity evidence, not a proof of robust convergence or real operating feasibility. Unlimited horizon, no rest rules, no 3D packing or truck-access checks.
