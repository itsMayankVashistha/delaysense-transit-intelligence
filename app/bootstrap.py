from pathlib import Path
import joblib

from app.config.settings import (
    BASELINE_TABLE_PATH,
    MODEL_PATH,
    FORCE_MOCK_MODEL,
    ENABLE_INTELLIGENCE,
    BASE_DIR,
    MODEL_FEATURES,
)
from app.services.baseline_service import BaselineService
from app.services.rolling_cache import RollingCache
from app.services.feature_pipeline import FeaturePipeline
from app.services.mock_model import MockModel
from app.services.inference_service import InferenceService


def _load_model():
    if FORCE_MOCK_MODEL:
        print("Using mock model because FORCE_MOCK_MODEL=true")
        return MockModel(), "mock"

    if Path(MODEL_PATH).exists():
        try:
            model = joblib.load(MODEL_PATH)
            print(f"Loaded real model from: {MODEL_PATH}")
            return model, "joblib"
        except Exception as e:
            print(f"Warning: failed to load model.joblib, falling back to mock model: {e}")

    print("Using mock model because no valid model.joblib was found")
    return MockModel(), "mock"


def _load_intelligence_layer():
    if not ENABLE_INTELLIGENCE:
        print("Intelligence layer disabled by config")
        return None

    try:
        from app.services.intelligence_layer import IntelligenceLayer
    except ImportError:
        print("Warning: intelligence_layer not found, continuing without it.")
        return None

    dataset_path = BASE_DIR / "data" / "data.parquet"
    if not dataset_path.exists():
        print("Warning: intelligence dataset not found, continuing without intelligence layer.")
        return None

    try:
        print(f"Loading intelligence layer from dataset: {dataset_path}")
        return IntelligenceLayer(str(dataset_path))
    except Exception as e:
        print(f"Warning: failed to initialize intelligence layer: {e}")
        return None


def _smoke_test_model(model, model_source):
    try:
        dummy_row = [[0.0 for _ in MODEL_FEATURES]]
        out = model.predict_proba(dummy_row)

        if not isinstance(out, (list, tuple)) and not hasattr(out, "__getitem__"):
            raise ValueError("predict_proba output is not indexable")

        _ = out[0][1]
        print(f"Model smoke test passed for model source: {model_source}")
    except Exception as e:
        raise RuntimeError(f"Model smoke test failed for model source '{model_source}': {e}")


def create_services():
    baseline_service = BaselineService(BASELINE_TABLE_PATH)
    rolling_cache = RollingCache(window_minutes=10)
    feature_pipeline = FeaturePipeline(baseline_service, rolling_cache)

    model, model_source = _load_model()
    _smoke_test_model(model, model_source)

    intelligence_layer = _load_intelligence_layer()

    inference_service = InferenceService(
        model=model,
        pipeline=feature_pipeline,
        intelligence_layer=intelligence_layer,
        model_source=model_source,
    )

    return {
        "baseline_service": baseline_service,
        "rolling_cache": rolling_cache,
        "feature_pipeline": feature_pipeline,
        "model": model,
        "model_source": model_source,
        "intelligence_layer": intelligence_layer,
        "inference_service": inference_service,
    }