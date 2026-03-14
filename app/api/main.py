from fastapi import FastAPI
from app.bootstrap import create_services

app = FastAPI(title="TfL Delay Intelligence API")

services = create_services()
inference_service = services["inference_service"]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sample")
def sample_prediction():
    raw_row = {
        "observed_at": 1772357400000,
        "stop_id": "940GZZLUOXC",
        "stop_name": "Oxford Circus",
        "line_id": "victoria",
        "direction": "northbound",
        "platform_name": "Northbound Platform",
        "destination_name": "Walthamstow Central",
        "time_to_station": 660,
    }

    result = inference_service.predict(raw_row)
    return result


@app.post("/predict")
def predict(row: dict):
    result = inference_service.predict(row)
    return result