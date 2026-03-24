from app.config.settings import ALERT_MODES, DEFAULT_ALERT_MODE, MODEL_FEATURES


class InferenceService:
    def __init__(self, model, pipeline, intelligence_layer=None, model_source="unknown"):
        self.model = model
        self.pipeline = pipeline
        self.intelligence_layer = intelligence_layer
        self.model_source = model_source

    def _score_risk(self, prob, mode_name):
        mode = ALERT_MODES[mode_name]

        if prob >= mode["high_threshold"]:
            return "high"
        elif prob >= mode["medium_threshold"]:
            return "medium"
        return "low"

    def _build_user_explanation(self, feat, prob, risk):
        current_min = feat["time_to_station"] / 60
        baseline_min = feat["baseline_median_tts"] / 60
        deviation_min = feat["deviation_from_baseline"] / 60

        if risk == "high":
            return (
                f"Current arrival estimate is {current_min:.1f} minutes, "
                f"which is {deviation_min:.1f} minutes above the usual "
                f"{baseline_min:.1f} minutes for this context. "
                f"The system flags this as high delay risk."
            )

        if risk == "medium":
            return (
                f"Current arrival estimate is {current_min:.1f} minutes, "
                f"which is above the usual {baseline_min:.1f} minutes. "
                f"The system detects elevated delay risk."
            )

        return (
            f"Current arrival estimate is {current_min:.1f} minutes, "
            f"which is close to the usual {baseline_min:.1f} minutes. "
            f"The system considers delay risk low."
        )

    def _build_model_input(self, model_features):
        return [[model_features[col] for col in MODEL_FEATURES]]

    def predict(self, raw_row, alert_mode=None, include_intelligence=True):
        alert_mode = alert_mode or DEFAULT_ALERT_MODE

        if alert_mode not in ALERT_MODES:
            alert_mode = DEFAULT_ALERT_MODE

        built = self.pipeline.build(raw_row)
        model_features = built["model_features"]
        context = built["context"]

        model_input = self._build_model_input(model_features)
        prob = float(self.model.predict_proba(model_input)[0][1])

        risk = self._score_risk(prob, alert_mode)
        alert_flag = prob >= ALERT_MODES[alert_mode]["alert_threshold"]

        explanation = self._build_user_explanation(model_features, prob, risk)

        result = {
            "prob": prob,
            "risk": risk,
            "alert_flag": bool(alert_flag),
            "alert_mode": alert_mode,
            "model_source": self.model_source,
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