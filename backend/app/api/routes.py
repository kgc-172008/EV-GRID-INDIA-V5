from fastapi import APIRouter, HTTPException
from ..core.config import GAP_WEIGHTS, DEFAULT_TARGET_EV_PER_CHARGER, DEMO_MODE
from ..core.schemas import PlanningConfig, ForecastRequest, ScenarioRequest
from ..data import load_data, latest_snapshot, data_quality
from ..gis.analysis import gap_analysis, candidate_recommendations
from ..dsa.algorithms import kd_nearest, priority_queue_rank
from ..ml.models import forecast, cluster_demand, predict_station_load

router = APIRouter(prefix="/api")


def get_context(target=DEFAULT_TARGET_EV_PER_CHARGER):
    reg, chg, reg_mode, chg_mode = load_data()
    snap, year = latest_snapshot(reg, chg)
    snap = gap_analysis(snap, target, chg, GAP_WEIGHTS)
    return reg, chg, snap, year, reg_mode, chg_mode


@router.get("/health")
def health():
    return {"status": "ok", "version": "5.0.0", "demo_mode": DEMO_MODE}


@router.get("/summary")
def summary(target: int = DEFAULT_TARGET_EV_PER_CHARGER):
    _, _, snap, year, rm, cm = get_context(target)
    return {
        "year": year,
        "ev_registrations": int(snap.ev_count.sum()),
        "chargers": int(snap.chargers.sum()),
        "ev_per_charger": round(float(snap.ev_count.sum() / max(snap.chargers.sum(), 1)), 2),
        "high_critical_zones": int(snap.gap_level.isin(["High", "Critical"]).sum()),
        "estimated_extra_chargers": int(snap.charger_gap.sum()),
        "data_mode": {"registrations": rm, "chargers": cm},
    }


@router.get("/zones")
def zones(target: int = DEFAULT_TARGET_EV_PER_CHARGER, state: str = "All India"):
    _, _, snap, year, _, _ = get_context(target)
    if state != "All India":
        snap = snap[snap.state == state]
    cols = [
        "state", "district", "year", "ev_count", "chargers", "ev_per_charger",
        "required_chargers", "charger_gap", "nearest_charger_km", "gap_score",
        "gap_level", "latitude", "longitude"
    ]
    return {"year": year, "rows": snap[cols].fillna("").to_dict(orient="records")}


@router.get("/chargers")
def chargers():
    _, chg, _, mode = load_data()
    return {"data_mode": mode, "rows": chg.fillna("").to_dict(orient="records")}


@router.get("/recommendations")
def recommendations(target: int = DEFAULT_TARGET_EV_PER_CHARGER, limit: int = 10):
    _, _, snap, _, _, _ = get_context(target)
    rec = candidate_recommendations(snap).head(max(1, min(limit, 100))).copy()
    return {
        "rows": rec[[
            "rank", "state", "district", "site_score", "gap_score",
            "charger_gap", "additional_chargers", "why_here", "latitude", "longitude"
        ]].to_dict(orient="records")
    }


@router.get("/dsa-analysis")
def dsa_analysis(target: int = DEFAULT_TARGET_EV_PER_CHARGER, limit: int = 10):
    """Transparent DSA layer using KD-tree nearest-neighbour search and a priority queue.

    This prototype does not claim a verified national road graph. It uses geographic
    point distances from the available charger dataset and clearly labels the method.
    """
    _, chg, snap, _, _, _ = get_context(target)
    points = chg[["latitude", "longitude"]].astype(float).to_numpy().tolist() if len(chg) else []
    ranked = candidate_recommendations(snap).copy()

    distances = []
    for r in ranked.itertuples():
        if not points:
            distances.append(None)
            continue
        idx = kd_nearest(points, [float(r.latitude), float(r.longitude)], k=1)[0]
        lat, lon = points[idx]
        # Lightweight coordinate distance for the prototype; gap_analysis has the
        # haversine calculation used for the primary nearest-charger field.
        distances.append(float(r.nearest_charger_km))

    ranked["nearest_charger_km_dsa"] = distances
    ranked["dsa_access_score"] = (
        (100 - ranked["nearest_charger_km_dsa"].fillna(ranked["nearest_charger_km_dsa"].median()).clip(lower=0) * 8)
        .clip(0, 100)
        .round(1)
    )
    ranked["final_priority"] = (
        0.65 * ranked["site_score"] + 0.35 * ranked["dsa_access_score"]
    ).round(1)
    ranked["dsa_method"] = "KD-tree nearest charger + priority queue ranking"
    ranked["road_graph_status"] = "NOT CONNECTED — geographic prototype"

    items = ranked[[
        "rank", "state", "district", "final_priority", "site_score",
        "dsa_access_score", "nearest_charger_km_dsa", "charger_gap",
        "additional_chargers", "why_here", "latitude", "longitude",
        "dsa_method", "road_graph_status"
    ]].to_dict(orient="records")
    return {"rows": priority_queue_rank(items, "final_priority")[:max(1, min(limit, 50))]}


@router.get("/clusters")
def clusters(target: int = DEFAULT_TARGET_EV_PER_CHARGER, n_clusters: int = 4):
    _, _, snap, _, _, _ = get_context(target)
    c = cluster_demand(snap, n_clusters)
    return {"rows": c[["state", "district", "cluster", "ev_count", "chargers", "charger_gap"]].to_dict(orient="records")}


@router.post("/forecast")
def run_forecast(req: ForecastRequest):
    reg, chg, _, _, _, _ = get_context(req.target_ev_per_charger)

    charger_counts = (
        chg.groupby(["state", "district"])
        .size()
        .reset_index(name="chargers")
    )
    reg_forecast = reg.merge(charger_counts, on=["state", "district"], how="left")
    reg_forecast["chargers"] = reg_forecast["chargers"].fillna(0).astype(int)

    try:
        fut, metrics = forecast(reg_forecast, req.horizon)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    latest = chg.groupby(["state", "district"]).size().reset_index(name="chargers")
    fut = fut.merge(latest, on=["state", "district"], how="left", suffixes=("", "_existing"))
    fut["chargers"] = fut["chargers_existing"].fillna(fut["chargers"])
    fut = fut.drop(columns=["chargers_existing"], errors="ignore")
    fut["required_chargers"] = (fut["predicted_ev"] / req.target_ev_per_charger).apply(__import__("math").ceil)
    fut["additional_chargers"] = (fut["required_chargers"] - fut["chargers"]).clip(lower=0)
    return {"metrics": metrics, "rows": fut.to_dict(orient="records"), "data_status": "DEMO/SYNTHETIC"}


@router.post("/scenario")
def scenario(req: ScenarioRequest):
    _, _, snap, year, _, _ = get_context(req.target_ev_per_charger)
    current = float(snap.ev_count.sum())
    chargers = int(snap.chargers.sum())
    rows = []
    for name, growth in [("Low", req.low_growth), ("Base", req.base_growth), ("High", req.high_growth)]:
        projected = current * ((1 + growth / 100) ** req.years)
        required = int(__import__("math").ceil(projected / req.target_ev_per_charger))
        rows.append({
            "scenario": name, "growth_percent": growth,
            "projected_evs": round(projected), "required_chargers": required,
            "additional_chargers": max(0, required - chargers)
        })
    return {"base_year": year, "rows": rows, "data_status": "DEMO/SYNTHETIC"}


@router.get("/load-prediction")
def load_prediction(traffic_index: float = 50, current_occupancy: float = 50, arrivals_index: float = 50):
    return predict_station_load({
        "traffic_index": traffic_index,
        "current_occupancy": current_occupancy,
        "arrivals_index": arrivals_index,
    })


@router.get("/quality")
def quality():
    reg, chg, _, _ = load_data()
    q = data_quality(reg, chg)
    q["data_status"] = "DEMO/SYNTHETIC" if DEMO_MODE else "REAL IMPORTED"
    q["limitations"] = [
        "Demo/synthetic records are used when verified CSV datasets are absent.",
        "Road-network routing is not connected to a verified national graph.",
        "Station load prediction is heuristic until historical session data is supplied.",
    ]
    return q
