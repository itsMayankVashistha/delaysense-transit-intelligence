from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from app.bootstrap import create_services

app = FastAPI(title="TfL Delay Intelligence API")

services = create_services()
inference_service = services["inference_service"]


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


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_source": services["model_source"],
        "intelligence_enabled": services["intelligence_layer"] is not None,
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