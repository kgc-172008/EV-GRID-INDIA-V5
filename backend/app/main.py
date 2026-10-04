from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .core.config import CORS_ORIGINS

app=FastAPI(
    title="EV-GRID INDIA V4 API",
    version="4.0.0",
    description="GIS + DSA + ML EV charging planning intelligence API."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "name":"EV-GRID INDIA",
        "version":"V4",
        "message":"WHERE + HOW MANY + WHY"
    }
