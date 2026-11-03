# Routes over the street map

Fixes unscoped global SVG styles that could affect Leaflet overlays. The standalone graph now uses svg.offline-map styling only. The interactive map uses a canvas renderer, waits for map CSS before initialization, invalidates its container size, then fits the actual 251 depot/customer coordinates. Both route pages support five vehicle layers and a 'Fit all routes' button. A vehicle with no assigned trips has an empty layer. The backup offline graph collapses when the interactive map opens.

## Open
Keep serve_map.py alongside the two HTML files. Open a terminal in that folder and run `py serve_map.py` (or `python serve_map.py`). Leave the terminal running. In the opened page click 'Open routes on street map (internet)'. To return to the delivery area after zooming, click 'Fit all routes'. Direct file opening retains the offline graph and disables online tiles because web tile requests require a valid Referer. Tile errors still retain local vector road geometry; no automatic retries or block evasion is implemented.

## Project update
Upload these patch files to the root of the SAME open Budapest OSM branch. Replace map_budapest.py and both generated HTML files; add/update serve_map.py. Do not change solver.py, matrices or experiment results for this display-only fix. An existing PR updates automatically.

## Validation and limits
Node-based Leaflet API mocks pass for both pages: geographic bounds, road-path overlay creation, five vehicle groups, toggles, backup collapse and absence of unscoped SVG rules. This is not a real-browser or live tile availability test. The environment's Chromium download failed, so visual overlay verification in the user's browser is still required. No OSM tiles were requested by these tests. Browser/node installation is not needed to use the HTML; Python starts the optional localhost server.
