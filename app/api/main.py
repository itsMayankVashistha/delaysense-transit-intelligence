from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.bootstrap import create_services
from app.services.tfl_api_service import TfLApiService, DEFAULT_MONITORED_STOPS

app = FastAPI(title="TfL Delay Intelligence API")

services = create_services()
inference_service = services["inference_service"]
tfl_api_service = TfLApiService()


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
def monitor_live(
    max_per_stop: int = 3,
    alert_mode: Optional[str] = None,
    include_intelligence: bool = True,
):
    rows = tfl_api_service.fetch_demo_monitored_arrivals(
        stop_ids=list(DEFAULT_MONITORED_STOPS.keys()),
        max_per_stop=max_per_stop,
    )

    predictions = [
        inference_service.predict(
            row,
            alert_mode=alert_mode,
            include_intelligence=include_intelligence,
        )
        for row in rows
    ]

    return {
        "source": "tfl_live",
        "count": len(predictions),
        "monitored_stops": DEFAULT_MONITORED_STOPS,
        "results": predictions,
    }


@app.post("/monitor/live")
def monitor_live_post(req: LiveMonitorRequest):
    stop_ids = req.stop_ids or list(DEFAULT_MONITORED_STOPS.keys())

    rows = tfl_api_service.fetch_arrivals_for_stops(
        stop_ids=stop_ids,
        max_per_stop=req.max_per_stop,
    )

    predictions = [
        inference_service.predict(
            row,
            alert_mode=req.alert_mode,
            include_intelligence=req.include_intelligence,
        )
        for row in rows
    ]

    return {
        "source": "tfl_live",
        "count": len(predictions),
        "requested_stop_ids": stop_ids,
        "results": predictions,
    }