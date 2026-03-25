from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import joblib


@dataclass
class LoadedModelArtifact:
    raw_object: Any
    model_object: Any
    artifact_type: str  # "plain_model" or "packaged_payload"
    model_name: str
    model_family: Optional[str] = None
    mode_name: Optional[str] = None
    threshold: Optional[float] = None
    horizon_seconds: Optional[int] = None
    features: List[str] = field(default_factory=list)
    input_type: Optional[str] = None
    positive_class_index: int = 1
    predict_method: str = "predict_proba"
    metadata: Dict[str, Any] = field(default_factory=dict)
    feature_contract: Dict[str, Any] = field(default_factory=dict)
    validation_examples_path: Optional[str] = None
    source_path: Optional[str] = None

    def predict_proba(self, X):
        if not hasattr(self.model_object, "predict_proba"):
            raise AttributeError(
                f"Loaded model '{self.model_name}' does not support predict_proba."
            )
        return self.model_object.predict_proba(X)


def _safe_load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _infer_artifact_type(obj: Any) -> str:
    if isinstance(obj, dict) and "pipeline" in obj:
        return "packaged_payload"
    return "plain_model"


def load_model_artifact(model_path: Union[str, Path]) -> LoadedModelArtifact:
    model_path = Path(model_path)
    obj = joblib.load(model_path)

    artifact_type = _infer_artifact_type(obj)

    metadata_path = model_path.with_suffix(".metadata.json")
    features_path = model_path.with_suffix(".features.json")
    validation_examples_path = model_path.with_suffix(".validation_examples.csv")

    metadata = _safe_load_json(metadata_path)
    feature_contract = _safe_load_json(features_path)

    if artifact_type == "packaged_payload":
        model_object = obj["pipeline"]
        model_name = obj.get("model_name", model_path.stem)
        mode_name = obj.get("mode")
        threshold = obj.get("threshold")
        horizon_seconds = obj.get("horizon_seconds")
        features = list(obj.get("features", []))
    else:
        model_object = obj
        model_name = metadata.get("model_name", model_path.stem)
        mode_name = metadata.get("mode_name")
        threshold = metadata.get("threshold_used_for_mode")
        horizon_seconds = metadata.get("horizon_seconds")
        features = list(
            metadata.get("feature_order")
            or feature_contract.get("feature_order")
            or []
        )

    input_type = (
        metadata.get("input_type")
        or feature_contract.get("input_type")
        or "dataframe"
    )

    positive_class_index = int(metadata.get("positive_class_index", 1))
    predict_method = metadata.get("predict_method", "predict_proba")
    model_family = metadata.get("model_family")

    return LoadedModelArtifact(
        raw_object=obj,
        model_object=model_object,
        artifact_type=artifact_type,
        model_name=model_name,
        model_family=model_family,
        mode_name=mode_name,
        threshold=threshold,
        horizon_seconds=horizon_seconds,
        features=features,
        input_type=input_type,
        positive_class_index=positive_class_index,
        predict_method=predict_method,
        metadata=metadata,
        feature_contract=feature_contract,
        validation_examples_path=str(validation_examples_path) if validation_examples_path.exists() else None,
        source_path=str(model_path),
    )