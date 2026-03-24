from app.bootstrap import create_services

raw_row = {
    "observed_at": 1772357400000,
    "stop_id": "940GZZLUOXC",
    "line_id": "victoria",
    "direction": "northbound",
    "time_to_station": 660,
}

services = create_services()
result = services["inference_service"].predict(raw_row)

print(result)