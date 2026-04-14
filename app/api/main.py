import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.bootstrap import create_services
from app.services.tfl_api_service import DEFAULT_MONITORED_STOPS

services = create_services()
inference_service = services["inference_service"]
live_monitor_manager = services["live_monitor_manager"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting background live monitor manager...")
    live_monitor_manager.start()
    try:
        yield
    finally:
        print("Stopping background live monitor manager...")
        live_monitor_manager.stop()


app = FastAPI(
    title="DelaySense API",
    lifespan=lifespan,
)

_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8501")
_origins = [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    observed_at: int
    stop_id: str
    stop_name: Optional[str] = "Unknown station"
    line_id: str
    vehicle_id: Optional[str] = None
    direction: str
    platform_name: Optional[str] = "Unknown platform"
    destination_name: Optional[str] = "Unknown destination"
    time_to_station: float
    alert_mode: Optional[str] = None
    include_intelligence: Optional[bool] = True


class LiveMonitorRequest(BaseModel):
    stop_ids: Optional[List[str]] = Field(default=None)
    max_per_stop: int = Field(default=3, ge=1, le=10)
    alert_mode: Optional[str] = None
    include_intelligence: Optional[bool] = True


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_source": services["model_source"],
        "intelligence_enabled": services["intelligence_layer"] is not None,
        "model_info": services.get("model_info"),
        "monitor_status": live_monitor_manager.get_status(),
        "default_monitored_stops": DEFAULT_MONITORED_STOPS,
    }


@app.get("/sample")
def sample_prediction():
    raw_row = {
        "observed_at": 1772357400000,
        "stop_id": "940GZZLUOXC",
        "stop_name": "Oxford Circus",
        "line_id": "victoria",
        "vehicle_id": "demo_vehicle_001",
        "direction": "northbound",
        "platform_name": "Northbound Platform",
        "destination_name": "Walthamstow Central",
        "time_to_station": 660,
    }
    return inference_service.predict(raw_row)


@app.post("/predict")
def predict(req: PredictRequest):
    row = req.model_dump()
    alert_mode = row.pop("alert_mode", None)
    include_intelligence = row.pop("include_intelligence", True)

    return inference_service.predict(
        row,
        alert_mode=alert_mode,
        include_intelligence=include_intelligence,
    )


@app.get("/monitor/live")
def monitor_live():
    results = live_monitor_manager.get_latest_results()
    status = live_monitor_manager.get_status()

    return {
        "source": "tfl_live",
        "count": len(results),
        "status": status,
        "monitored_stops": DEFAULT_MONITORED_STOPS,
        "results": results,
    }


@app.get("/monitor/status")
def monitor_status():
    return live_monitor_manager.get_status()

@app.get("/")
def root():
    return {
        "project": "DelaySense - Transit Intelligence System",
        "status": "ok",
        "summary": "Real-time ML-powered early warning system for short-horizon London Underground delay risk.",
        "available_endpoints": {
            "docs": "/docs",
            "health": "/health",
            "sample": "/sample",
            "predict": "/predict",
            "live_monitor": "/monitor/live"
        }
    }


@app.post("/monitor/refresh")
def monitor_refresh():
    live_monitor_manager.poll_once()
    results = live_monitor_manager.get_latest_results()
    status = live_monitor_manager.get_status()

    return {
        "source": "tfl_live_manual_refresh",
        "count": len(results),
        "status": status,
        "results": results,
    }