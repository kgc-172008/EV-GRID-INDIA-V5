# EV-GRID INDIA V5

**EV charging infrastructure decision intelligence — React + FastAPI + ML + GIS + DSA prototype**

V5 upgrades the working V4 prototype into a clearer decision dashboard focused on:

- **WHERE** is charging infrastructure underserved?
- **HOW MANY** additional chargers are needed?
- **WHY** is a location prioritized?

## What is new in V5

1. **Explainable recommendation view** — shows the reasons behind each ranked location.
2. **DSA analysis** — KD-tree nearest-charger search + priority-queue ranking, explicitly labelled as a geographic prototype rather than verified road routing.
3. **Interactive GIS dashboard** — gap zones, charger points and top recommendations on one map.
4. **ML forecast view** — future EV demand plus required/additional charger calculations.
5. **Scenario planning** — Low/Base/High growth comparison.
6. **Demand clustering** — K-Means cluster summary.
7. **Station-load page** — transparent heuristic fallback until historical station-session data is connected.
8. **Data provenance warning** — DEMO/SYNTHETIC status and limitations are visible in the dashboard.
9. **Cleaner navigation** — Overview, Map, Gap, Recommendations, DSA, Forecast, Scenarios, Clusters, Load and Quality.

## Important data limitation

The included dataset is **DEMO/SYNTHETIC** when verified CSVs are absent. Do not present demo numbers as live government or operator data.

The project does **not** fabricate:

- live charger availability,
- real-time traffic,
- a verified national road graph,
- historical charger-session training data,
- authenticated government/operator feeds.

The DSA layer currently uses geographic nearest-neighbour analysis. A production road-routing layer can later replace this with a verified road graph and A*/Dijkstra travel-time costs.

## Run with Docker

From the extracted `EV_GRID_INDIA_V5` folder:

```powershell
# If the older V4 stack is running, stop it first so port 8000/5173 are free.
cd "C:\path\to\EV_GRID_INDIA_V5"
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

Keep the Docker terminal running while using the dashboard.

## Main API endpoints

- `GET /api/health`
- `GET /api/summary`
- `GET /api/zones`
- `GET /api/chargers`
- `GET /api/recommendations`
- `GET /api/dsa-analysis`
- `GET /api/clusters`
- `POST /api/forecast`
- `POST /api/scenario`
- `GET /api/load-prediction`
- `GET /api/quality`

## Recommended demo flow

1. Open **Overview** and explain WHERE + HOW MANY + WHY.
2. Open **Map** and show Critical/High zones and charger points.
3. Open **Recommendations** and click through the reasons for top locations.
4. Open **DSA** and explain KD-tree + priority queue.
5. Run **Forecast** and explain predicted EV demand and additional chargers.
6. Open **Scenarios** for Low/Base/High planning assumptions.
7. Open **Quality** and explicitly disclose DEMO/SYNTHETIC status.

## Production roadmap

### Phase 1 — verified data
- verified EV registration datasets,
- verified charger inventory,
- state/district master data,
- timestamps and source metadata.

### Phase 2 — real GIS/DSA
- road graph,
- A*/Dijkstra travel-time routing,
- service-area/corridor analysis,
- network-aware candidate selection.

### Phase 3 — live integrations
- authenticated operator/OCPI-compatible charger status,
- traffic provider,
- historical station sessions,
- monitoring and data-quality alerts.

### Phase 4 — advanced optimization
- budget-constrained facility location,
- demand coverage optimization,
- uncertainty/confidence reporting,
- cloud deployment and observability.

**V5 is a planning prototype, not a construction approval or live national control system.**
