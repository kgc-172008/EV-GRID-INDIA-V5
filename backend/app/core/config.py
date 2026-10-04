import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://evgrid:evgrid@localhost:5432/evgrid",
)
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
DEFAULT_TARGET_EV_PER_CHARGER = 150

GAP_WEIGHTS = {
    "ev_demand": 0.35,
    "ev_per_charger": 0.20,
    "population_demand": 0.15,
    "road_mobility": 0.15,
    "activity": 0.10,
    "access_pressure": 0.05,
}
