# EV-GRID INDIA V5 — Requirements

## Functional
1. National interactive GIS map.
2. EV registration and charger integration.
3. Current charging-gap analysis.
4. Configurable EV/charger planning target.
5. Future EV demand forecasting.
6. Charger requirement forecasting.
7. Explainable site recommendations.
8. Scenario analysis.
9. Data quality/provenance.
10. DSA-powered spatial/ranking modules.
11. ML-powered forecasting and clustering.
12. Live station-load interface with explicit data-status labeling.
13. API-first architecture.
14. 2D map now; 3D/traffic provider integration point prepared for next integration.

## DSA
- Dijkstra
- A*
- Priority Queue
- KD-Tree
- Greedy site selection
- Graph/corridor analysis extension point

## ML
- Random Forest forecast
- chronological holdout metrics
- K-Means demand clustering
- station-load prediction interface
- future extension: XGBoost comparison, trained load model

## Data
- VAHAN/vehicle registration imports
- charger inventory
- road/context features
- source and retrieval date
- synthetic data must remain labeled

## Architecture
React -> FastAPI -> GIS/DSA/ML -> PostgreSQL/PostGIS

## Not yet represented as real data
- authenticated live operator feeds
- verified national road graph
- live traffic provider
- actual 3D map provider credentials
- actual historical charger-session data

Those require external credentials/data sources and are intentionally represented as integration points rather than fabricated live data.
