from __future__ import annotations

import pandas as pd

from app.config.settings import ALERT_MODES, DEFAULT_ALERT_MODE, MODEL_FEATURES


class InferenceService:
    def __init__(
        self,
        model,
        pipeline,
        intelligence_layer=None,
        model_source="unknown",
        model_info=None,
    ):
        self.model = model
        self.pipeline = pipeline
        self.intelligence_layer = intelligence_layer
        self.model_source = model_source
        self.model_info = model_info or {}

    def _get_feature_order(self):
        return self.model_info.get("features") or MODEL_FEATURES

    def _get_input_type(self):
        return (self.model_info.get("input_type") or "array").lower()

    def _get_positive_class_index(self):
        return int(self.model_info.get("positive_class_index", 1))

        '''    def _get_artifact_threshold(self):
                threshold = self.model_info.get("threshold")
                if threshold is None:
                    return None
                return float(threshold)'''

    def _resolve_alert_mode(self, alert_mode):
        alert_mode = alert_mode or DEFAULT_ALERT_MODE
        if alert_mode not in ALERT_MODES:
            return DEFAULT_ALERT_MODE
        return alert_mode

    def _score_risk(self, prob, mode_name):
        mode = ALERT_MODES[mode_name]

        if prob >= mode["high_threshold"]:
            return "high"
        elif prob >= mode["medium_threshold"]:
            return "medium"
        return "low"


    def _resolve_alert_threshold(self, alert_mode):
        return float(ALERT_MODES[alert_mode]["alert_threshold"])

    def _format_minutes_value(self, minutes):
        total_seconds = int(round(minutes * 60))

        if total_seconds < 60:
            return f"{total_seconds}s"

        mins = total_seconds // 60
        secs = total_seconds % 60

        if secs == 0:
            return f"{mins}m"

        return f"{mins}m {secs}s"

    def _build_user_explanation(self, feat, prob, risk):
        current_time = self._format_minutes_value(feat["time_to_station"] / 60)
        baseline_time = self._format_minutes_value(feat["baseline_median_tts"] / 60)
        deviation_time = self._format_minutes_value(abs(feat["deviation_from_baseline"]) / 60)

        if risk == "high":
            return (
                f"Current arrival estimate is {current_time}, "
                f"which is {deviation_time} above the usual "
                f"{baseline_time} for this context. "
                f"The system flags this as high delay risk."
            )

        if risk == "medium":
            return (
                f"Current arrival estimate is {current_time}, "
                f"which is above the usual {baseline_time}. "
                f"The system detects elevated delay risk."
            )

        return (
            f"Current arrival estimate is {current_time}, "
            f"which is close to the usual {baseline_time}. "
            f"The system considers delay risk low."
        )

    def _build_model_input(self, model_features):
        feature_order = self._get_feature_order()
        input_type = self._get_input_type()

        missing = [col for col in feature_order if col not in model_features]
        if missing:
            raise ValueError(
                f"Model input cannot be built because required features are missing: {missing}"
            )

        if input_type == "dataframe":
            return pd.DataFrame([{col: model_features[col] for col in feature_order}])

        return [[model_features[col] for col in feature_order]]

    def _predict_probability(self, model_input):
        if not hasattr(self.model, "predict_proba"):
            raise AttributeError("Loaded model does not expose predict_proba")

        proba = self.model.predict_proba(model_input)

        positive_idx = self._get_positive_class_index()

        try:
            return float(proba[0][positive_idx])
        except Exception as e:
            raise RuntimeError(
                f"Failed to extract positive class probability at index {positive_idx}: {e}"
            )

    def predict(self, raw_row, alert_mode=None, include_intelligence=True):
        alert_mode = self._resolve_alert_mode(alert_mode)

        built = self.pipeline.build(raw_row)
        model_features = built["model_features"]
        context = built["context"]

        model_input = self._build_model_input(model_features)
        prob = self._predict_probability(model_input)

        risk = self._score_risk(prob, alert_mode)
        alert_threshold = self._resolve_alert_threshold(alert_mode)
        alert_flag = prob >= alert_threshold

        explanation = self._build_user_explanation(model_features, prob, risk)

        result = {
            "prob": prob,
            "risk": risk,
            "alert_flag": bool(alert_flag),
            "alert_mode": alert_mode,
            "alert_threshold": alert_threshold,
            "model_source": self.model_source,
            "model_info": {
                "model_name": self.model_info.get("model_name"),
                "model_family": self.model_info.get("model_family"),
                "artifact_type": self.model_info.get("artifact_type"),
                "mode_name": self.model_info.get("mode_name"),
                "horizon_seconds": self.model_info.get("horizon_seconds"),
                "input_type": self._get_input_type(),
                "positive_class_index": self._get_positive_class_index(),
                "features": self._get_feature_order(),
                "source_path": self.model_info.get("source_path"),
            },
            "explanation": explanation,
            "display": context,
            "features": model_features,
        }

        if include_intelligence and self.intelligence_layer is not None:
            try:
                merged = {**context, **model_features}
                result["intelligence"] = self.intelligence_layer.build_intelligence_output(
                    features=merged,
                    prob=prob,
                    baseline=model_features["baseline_median_tts"],
                )
            except Exception as e:
                result["intelligence_error"] = str(e)

        return result