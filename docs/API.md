# API

Base URL: `http://localhost:8000/api`

GET `/health`
GET `/summary?target=150`
GET `/zones?target=150&state=All%20India`
GET `/chargers`
GET `/recommendations?target=150&limit=10`
GET `/clusters?target=150&n_clusters=4`
GET `/quality`
GET `/load-prediction?traffic_index=80&current_occupancy=70&arrivals_index=75`

POST `/forecast`
```json
{"target_ev_per_charger":150,"horizon":5}
```

POST `/scenario`
```json
{
  "target_ev_per_charger":150,
  "years":5,
  "low_growth":8,
  "base_growth":15,
  "high_growth":22
}
```

Interactive API documentation is available at `/docs`.
