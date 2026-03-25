from pathlib import Path
import pandas as pd

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
from app.services.artifact_loader import load_model_artifact


def _load_model():
    if FORCE_MOCK_MODEL:
        print("Using mock model because FORCE_MOCK_MODEL=true")
        return MockModel(), "mock", None
    print(f"Resolved MODEL_PATH: {Path(MODEL_PATH).resolve()}")
    print(f"MODEL_PATH exists: {Path(MODEL_PATH).exists()}")

    if Path(MODEL_PATH).exists():
        try:
            artifact = load_model_artifact(MODEL_PATH)
            print(f"Loaded real model artifact from: {MODEL_PATH}")
            print(f"Artifact type: {artifact.artifact_type}")
            print(f"Model name: {artifact.model_name}")
            print(f"Model family: {artifact.model_family}")
            print(f"Mode name: {artifact.mode_name}")
            print(f"Horizon: {artifact.horizon_seconds}")
            print(f"Input type: {artifact.input_type}")
            print(f"Threshold: {artifact.threshold}")
            print(f"Features: {artifact.features}")

            return artifact, "joblib", {
                "artifact_type": artifact.artifact_type,
                "model_name": artifact.model_name,
                "model_family": artifact.model_family,
                "mode_name": artifact.mode_name,
                "threshold": artifact.threshold,
                "horizon_seconds": artifact.horizon_seconds,
                "features": artifact.features,
                "input_type": artifact.input_type,
                "positive_class_index": artifact.positive_class_index,
                "metadata": artifact.metadata,
                "feature_contract": artifact.feature_contract,
                "source_path": artifact.source_path,
            }
        except Exception as e:
            print(f"Warning: failed to load model artifact, falling back to mock model: {e}")

    print("Using mock model because no valid model artifact was found")
    return MockModel(), "mock", None


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


def _smoke_test_model(model, model_source, model_info=None):
    try:
        if model_source == "mock":
            dummy_row = [[0.0 for _ in MODEL_FEATURES]]
            out = model.predict_proba(dummy_row)
        else:
            feature_names = (model_info or {}).get("features") or MODEL_FEATURES
            input_type = ((model_info or {}).get("input_type") or "dataframe").lower()

            if input_type == "dataframe":
                X_dummy = pd.DataFrame([{feature: 0.0 for feature in feature_names}])
            else:
                X_dummy = [[0.0 for _ in feature_names]]

            out = model.predict_proba(X_dummy)

        if not hasattr(out, "__getitem__"):
            raise ValueError("predict_proba output is not indexable")

        positive_idx = ((model_info or {}).get("positive_class_index", 1))
        _ = out[0][positive_idx]

        print(f"Model smoke test passed for model source: {model_source}")
    except Exception as e:
        raise RuntimeError(f"Model smoke test failed for model source '{model_source}': {e}")


def create_services():
    baseline_service = BaselineService(BASELINE_TABLE_PATH)
    rolling_cache = RollingCache(window_minutes=10)
    feature_pipeline = FeaturePipeline(baseline_service, rolling_cache)

    model, model_source, model_info = _load_model()
    _smoke_test_model(model, model_source, model_info)

    intelligence_layer = _load_intelligence_layer()

    inference_service = InferenceService(
        model=model,
        pipeline=feature_pipeline,
        intelligence_layer=intelligence_layer,
        model_source=model_source,
        model_info=model_info,
    )

    return {
        "baseline_service": baseline_service,
        "rolling_cache": rolling_cache,
        "feature_pipeline": feature_pipeline,
        "model": model,
        "model_source": model_source,
        "model_info": model_info,
        "intelligence_layer": intelligence_layer,
        "inference_service": inference_service,
    }