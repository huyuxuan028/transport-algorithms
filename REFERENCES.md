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

The existing literature list is retained. Subhan's proposed supplemental list
has not yet been received and must be reconciled before final documentation approval.
