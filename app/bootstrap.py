from app.config.settings import BASELINE_TABLE_PATH
from app.services.baseline_service import BaselineService
from app.services.rolling_cache import RollingCache
from app.services.feature_pipeline import FeaturePipeline
from app.services.mock_model import MockModel
from app.services.inference_service import InferenceService


def create_services():
    baseline_service = BaselineService(BASELINE_TABLE_PATH)
    rolling_cache = RollingCache(window_minutes=10)
    feature_pipeline = FeaturePipeline(baseline_service, rolling_cache)
    model = MockModel()
    inference_service = InferenceService(model, feature_pipeline)

    return {
        "baseline_service": baseline_service,
        "rolling_cache": rolling_cache,
        "feature_pipeline": feature_pipeline,
        "model": model,
        "inference_service": inference_service,
    }