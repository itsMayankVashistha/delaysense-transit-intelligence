from app.services.baseline_service import BaselineService
from app.services.rolling_cache import RollingCache
from app.services.feature_pipeline import FeaturePipeline
from app.services.mock_model import MockModel
from app.services.inference_service import InferenceService

# temporary fake baseline service if parquet not ready
class DummyBaselineService:
    def lookup(self, stop_id, line_id, direction, hour, weekday):
        return 240.0


raw_row = {
    "observed_at": 1772357400000,  # example timestamp in ms
    "stop_id": "940GZZLUOXC",
    "line_id": "victoria",
    "direction": "northbound",
    "time_to_station": 660,
}

baseline_service = DummyBaselineService()
rolling_cache = RollingCache(window_minutes=10)
feature_pipeline = FeaturePipeline(baseline_service, rolling_cache)
model = MockModel()
inference_service = InferenceService(model, feature_pipeline)

result = inference_service.predict(raw_row)

print(result)