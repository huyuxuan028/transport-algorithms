# Research and Data References

## Core and targeted publications

**[R1]** Prins, C. (2009). Two memetic algorithms for heterogeneous fleet vehicle
routing problems. Engineering Applications of Artificial Intelligence, 22(6),
916-928. https://doi.org/10.1016/j.engappai.2008.10.006

Insight: giant-tour chromosomes can be decoded into trips with vehicle assignment.
Directly relevant to fleet heterogeneity and order/allocation coupling. Our
explicit allocation vector is a simpler alternative, not an implementation of
Prins's full method.

**[R2]** Vidal, T. (2022). Hybrid genetic search for the CVRP: Open-source
implementation and SWAP* neighborhood. Computers & Operations Research, 140,
105643. https://doi.org/10.1016/j.cor.2021.105643
Open manuscript: https://arxiv.org/abs/2012.10384

Insight: combine population search with route improvement. Our bounded 2-opt and
small GA omit published HGS's adaptive penalties, advanced diversity management
and SWAP* implementation.

**[R3]** Zhao, J., Poon, M., Tan, V. Y. F., and Zhang, Z. (2024). A hybrid genetic
search and dynamic programming-based split algorithm for the multi-trip
time-dependent vehicle routing problem. European Journal of Operational Research,
317(3), 921-935. https://doi.org/10.1016/j.ejor.2024.04.011
Institutional record: https://publications.polymtl.ca/58549/

Insight: multi-trip and time dependence require a tailored splitting procedure.
We implement only constant-distance, unrestricted-horizon trips, not the paper's
time-dependent decoder or its acceleration method.

**[R4]** Penna, P. H. V., Subramanian, A., Ochi, L. S., Vidal, T., and Prins, C.
(2018 preprint). A Hybrid Heuristic for a Broad Class of Vehicle Routing Problems
with Heterogeneous Fleet. https://arxiv.org/abs/1803.01930

Insight: iterated local search, variable-neighborhood descent and set partitioning
offer an alternative family for heterogeneous rich VRPs. This family is reviewed,
not reproduced.

**[R5]** Zhao, W., Bian, X., and Mei, X. (2024). An Adaptive Multi-Objective Genetic
Algorithm for Solving Heterogeneous Green City Vehicle Routing Problem.
Applied Sciences, 14(15), 6594. https://doi.org/10.3390/app14156594

Insight: heterogeneity and environmental/operating objectives can be treated
jointly. Our fixed-rate fuel proxy is much simpler; no equivalent emissions or
time-window model is claimed.

**[R6]** Hvattum, L. M. (2025). Where to Split in Hybrid Genetic Search for the
Capacitated Vehicle Routing Problem. Algorithms, 18(3), 165.
https://doi.org/10.3390/a18030165

Insight: the starting point of a giant tour can affect the split and search.
Rotation-based tests are a potential refinement, not a measured feature here.

## Additional references supplied by the team

R7–R31 were contributed by the team as a literature shortlist. Inclusion does
not imply that every team member has read each full paper or reproduced its
method. Performance rankings and software capabilities in the notes require
source-specific checking before presentation.

### Problem identification and surveys

**[R7]** Dantzig, G. B., Ramser, J. H. (1959). The Truck Dispatching Problem.
Management Science, 6(1), 80-91. https://doi.org/10.1287/mnsc.6.1.80
Insight: origin of the capacitated VRP; our brief is a rich variant of this problem.

**[R8]** Koç, Ç., Bektaş, T., Jabali, O., Laporte, G. (2016). Thirty years of
heterogeneous vehicle routing. European Journal of Operational Research, 249(1), 1-21.
https://doi.org/10.1016/j.ejor.2015.07.020
Insight: survey and classification of fixed-fleet (HVRP) vs fleet-size-and-mix (FSM)
variants; our benchmark is the fixed-fleet case.

**[R9]** Cattaruzza, D., Absi, N., Feillet, D. (2016). Vehicle routing problems with
multiple trips. 4OR, 14(3), 223-259. https://doi.org/10.1007/s10288-016-0306-2
Insight: survey of multi-trip VRP; justifies sequential trips per vehicle in our decoder.

**[R10]** Lahyani, R., Khemakhem, M., Semet, F. (2015). Rich vehicle routing problems:
From a taxonomy to a definition. European Journal of Operational Research, 241(1), 1-14.
https://doi.org/10.1016/j.ejor.2014.07.048
Insight: our combination of fleet, capacity, time and cost attributes is a "rich VRP".

**[R11]** Pollaris, H., Braekers, K., Caris, A., Janssens, G. K., Limbourg, S. (2015).
Vehicle routing problems with loading constraints: state-of-the-art and future
directions. OR Spectrum, 37(2), 297-330. https://doi.org/10.1007/s00291-014-0386-3
Insight: covers weight/volume limits and 2D/3D loading; frames packing option 1 vs 2.

**[R12]** Chi, J., Song, X., He, Y. (2026). Capacitated Vehicle Routing Problems With
Three-Dimensional Loading Constraints: A Systematic Review and New Taxonomy.
IET Intelligent Transport Systems. https://doi.org/10.1049/itr2.70281
Insight: newest 3L-CVRP survey (2006-2026); starting point if packing option 2 is attempted.

### Genetic / memetic algorithms (basis of our representation and decoder)

**[R13]** Prins, C. (2004). A simple and effective evolutionary algorithm for the
vehicle routing problem. Computers & Operations Research, 31(12), 1985-2002.
https://doi.org/10.1016/S0305-0548(03)00158-8
Insight: giant-tour chromosome + optimal Split + local search; our DP Split follows this.

**[R14]** Vidal, T., Crainic, T. G., Gendreau, M., Prins, C. (2014). A unified solution
framework for multi-attribute vehicle routing problems. European Journal of
Operational Research, 234(3), 658-673. https://doi.org/10.1016/j.ejor.2013.09.045
Insight: one hybrid genetic search handling many attributes (duration, fleet, multi-trip)
through modular route evaluation.

**[R15]** Cattaruzza, D., Absi, N., Feillet, D., Vidal, T. (2014). A memetic algorithm
for the Multi Trip Vehicle Routing Problem. European Journal of Operational Research,
236(3), 833-848. https://doi.org/10.1016/j.ejor.2013.06.012
Insight: adapted Split for multi-trip; closest published GA to our setting.

**[R16]** Wouda, N. A., Lan, L., Kool, W. (2024). PyVRP: A High-Performance VRP Solver
Package. INFORMS Journal on Computing, 36(4), 943-955.
https://doi.org/10.1287/ijoc.2023.0055
Insight: open-source HGS supporting multiple capacities, shift duration with overtime
cost and reloads (multi-trip); candidate external method for the final comparison.

### Heterogeneous fleet: state of the art

**[R17]** Pessoa, A., Sadykov, R., Uchoa, E. (2018). Enhanced Branch-Cut-and-Price
algorithm for heterogeneous fleet vehicle routing problems. European Journal of
Operational Research, 270(2), 530-543. https://doi.org/10.1016/j.ejor.2018.04.009
Insight: leading exact method; defines what "optimal" means for HFVRP benchmarks.

**[R18]** Máximo, V. R., Cordeau, J.-F., Nascimento, M. C. V. (2022). An adaptive
iterated local search heuristic for the Heterogeneous Fleet Vehicle Routing Problem.
Computers & Operations Research, 148, 105954. https://doi.org/10.1016/j.cor.2022.105954
Insight: current best heuristic results on HFVRP; benchmark for local-search design.

**[R19]** Subramanian, A., Penna, P. H. V., Uchoa, E., Ochi, L. S. (2012). A hybrid
algorithm for the Heterogeneous Fleet Vehicle Routing Problem. European Journal of
Operational Research, 221(2), 285-295. https://doi.org/10.1016/j.ejor.2012.03.016
Insight: ILS + set partitioning over a route pool; the method R4 builds on.

### Multi-trip: recent algorithms

**[R20]** Yang, Y. (2023). An Exact Price-Cut-and-Enumerate Method for the Capacitated
Multitrip Vehicle Routing Problem with Time Windows. Transportation Science, 57(1),
230-251. https://doi.org/10.1287/trsc.2022.1161

**[R21]** Paradiso, R., Roberti, R., Laganà, D., Dullaert, W. (2020). An Exact Solution
Framework for Multitrip Vehicle-Routing Problems with Time Windows. Operations
Research, 68(1), 180-198. https://doi.org/10.1287/opre.2019.1874

**[R22]** François, V., Arda, Y., Crama, Y. (2019). Adaptive Large Neighborhood Search
for Multitrip Vehicle Routing with Time Windows. Transportation Science, 53(6),
1706-1730. https://doi.org/10.1287/trsc.2019.0909
Insight (R20-R22): exact and ALNS references for multi-trip; useful for the
"compare with other methods" requirement.

### Cost objective: wages, overtime, fuel

**[R23]** Koç, Ç., Bektaş, T., Jabali, O., Laporte, G. (2014). The fleet size and mix
pollution-routing problem. Transportation Research Part B, 70, 239-254.
https://doi.org/10.1016/j.trb.2014.09.008
Insight: heterogeneous fleet with a fuel + driver wage + vehicle cost objective;
closest published objective to ours.

**[R24]** Bektaş, T., Laporte, G. (2011). The Pollution-Routing Problem. Transportation
Research Part B, 45(8), 1232-1250. https://doi.org/10.1016/j.trb.2011.02.004
Insight: objective combining fuel and driver wage cost.

**[R25]** Ren, Y., Dessouky, M., Ordóñez, F. (2010). The multi-shift vehicle routing
problem with overtime. Computers & Operations Research, 37(11), 1987-1998.
https://doi.org/10.1016/j.cor.2010.01.016
Insight: shift length as a soft limit with paid overtime, as in our wage model.

### 3D loading (packing option 2, not implemented)

**[R26]** Gendreau, M., Iori, M., Laporte, G., Martello, S. (2006). A Tabu Search
Algorithm for a Routing and Container Loading Problem. Transportation Science, 40(3),
342-350. https://doi.org/10.1287/trsc.1050.0145
Insight: defines 3L-CVRP; the real instances came from an Italian furniture distributor.

**[R27]** Fuellerer, G., Doerner, K. F., Hartl, R. F., Iori, M. (2010). Metaheuristics
for vehicle routing problems with three-dimensional loading constraints. European
Journal of Operational Research, 201(3), 751-759.
https://doi.org/10.1016/j.ejor.2009.03.046
Insight: fast packing heuristics inside a routing metaheuristic; the pattern we would
use to add a loading check to Split.

**[R28]** Krebs, C., Ehmke, J. F., Koch, H. (2021). Advanced loading constraints for 3D
vehicle routing problems. OR Spectrum, 43, 835-875.
https://doi.org/10.1007/s00291-021-00645-w
Insight: realistic loading rules (stability, load bearing, axle weight) for furniture-like cargo.

**[R29]** Rojas-Saavedra, J. C., Álvarez-Martínez, D., Escobar, J. W. (2026).
Boosting sustainable development goals: a hybrid metaheuristic approach for the
heterogeneous vehicle routing problem with three-dimensional packing constraints and
fuel consumption. Annals of Operations Research, 358(1), 401-446.
https://doi.org/10.1007/s10479-023-05533-w
Insight: heterogeneous fleet + 3D packing + fuel in one model; the closest match to
the full brief.

**[R30]** Tamke, F., Linß, F., Kuttner, L., Buscher, U. (2026). A branch-and-cut
algorithm for vehicle routing problems with three-dimensional loading constraints.
European Journal of Operational Research, 331(3), 790-808.
https://doi.org/10.1016/j.ejor.2025.10.010
Insight: current exact method for 3L-VRP.

### Tooling

**[R31]** Helsgaun, K. (2017). An Extension of the Lin-Kernighan-Helsgaun TSP Solver for
Constrained Traveling Salesman and Vehicle Routing Problems. Technical Report,
Roskilde University. http://webhotel4.ruc.dk/~keld/research/LKH-3/LKH-3_REPORT.pdf
Insight: LKH-3 covers DCVRP, service times and min/max route size (MTSP_MIN_SIZE /
MTSP_MAX_SIZE) but not heterogeneous fleets, multi-trip or 3D loading; candidate
external comparison for a simplified sub-problem.

## Dataset and operational inputs

**[D1]** Crawl Feeds. Furniture products dataset from amazon (Kaggle).
https://www.kaggle.com/datasets/crawlfeeds/furniture-products-dataset-from-amazon
Public metadata: https://www.kaggle.com/api/v1/datasets/view/crawlfeeds/furniture-products-dataset-from-amazon
Provider description: https://crawlfeeds.com/datasets/furniture-products-dataset-from-amazon

The Kaggle API reports CC0: Public Domain; its snapshot and the original CSV
are retained in the generator repository. This is a sample, not the provider's
full commercial catalog. Use only the audited schema/interpretation described
in the generator README.

**[D2]** Instructor-provided vehicle parameter list: VW Caddy Cargo SWB (VW MY26
spec-sheet values), Mercedes Sprinter 315 CDI L2H2 (Vanaways/CAP HPI values), and
MAN TGL 12.190 box (Mascus/operator values). The exact values are reproduced in
`vehicles.json` as adopted course inputs; original specification URLs were not
provided and no independent manufacturer-source verification is claimed.


## Shared benchmark and routing sources

**[D3]** PSO team: https://github.com/xsilentkiller/industrial-transport
The common source is imported as `data/shared_pso_250.json`. Its CSV distances
are haversine times 1.3, NOT road-network distances. Source vehicle/cost/service
parameters are preserved. The importer snapshot reviewed here is blob
`106b9cd54b4c7e33cf6b29f4754380e7c1c7581b`; instance blob
`83cf5c206c297ee97e312c5f694cd98b794c4746`.

**[D4]** OpenStreetMap contributors. https://www.openstreetmap.org/copyright
Road data are ODbL. Public raw-data query guidance:
https://dev.overpass-api.de/overpass-doc/en/preface/commons.html

**[D5]** HeiGIT / GIScience. Openrouteservice Matrix Endpoint.
https://giscience.github.io/openrouteservice/api-reference/endpoints/matrix/
A matrix gives distances/times; detailed route geometry needs a separate directions
request or the same local graph. The measured results here use local OSM, not ORS.

The team-supplied additional literature list is integrated as R7–R31 above.
