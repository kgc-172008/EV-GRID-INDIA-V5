from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PlanningConfig(BaseModel):
    target_ev_per_charger: int = Field(150, ge=1, le=5000)

class ForecastRequest(PlanningConfig):
    horizon: int = Field(5, ge=1, le=10)

class ScenarioRequest(PlanningConfig):
    years: int = Field(5, ge=1, le=15)
    low_growth: float = Field(8, ge=0, le=100)
    base_growth: float = Field(15, ge=0, le=100)
    high_growth: float = Field(22, ge=0, le=100)

class RouteRequest(BaseModel):
    start_node: str
    end_node: str
    algorithm: str = "astar"

class RecommendationResponse(BaseModel):
    rank: int
    state: str
    district: str
    site_score: float
    gap_score: float
    charger_gap: int
    additional_chargers: int
    why_here: List[str]
    latitude: float
    longitude: float

class HealthResponse(BaseModel):
    status: str
    version: str
    demo_mode: bool
