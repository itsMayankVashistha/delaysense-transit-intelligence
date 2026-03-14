class InferenceService:

    def __init__(self, model, pipeline):
        self.model = model
        self.pipeline = pipeline

    def _build_user_explanation(self, raw_row, feat, prob, risk):
        current_min = feat["time_to_station"] / 60
        baseline_min = feat["baseline_median_tts"] / 60

        if risk == "high":
            return (
                f"Current arrival estimate is {current_min:.1f} minutes, "
                f"which is well above the usual {baseline_min:.1f} minutes "
                f"for this station and direction. The system flags this as high delay risk."
            )

        if risk == "medium":
            return (
                f"Current arrival estimate is {current_min:.1f} minutes, "
                f"compared with a usual {baseline_min:.1f} minutes. "
                f"The system detects elevated delay risk."
            )

        return (
            f"Current arrival estimate is {current_min:.1f} minutes, "
            f"which is close to the usual {baseline_min:.1f} minutes. "
            f"The system considers delay risk low."
        )

    def predict(self, raw_row):
        feat = self.pipeline.build(raw_row)
        prob = self.model.predict_proba([feat])[0][1]

        if prob > 0.7:
            risk = "high"
        elif prob > 0.3:
            risk = "medium"
        else:
            risk = "low"

        explanation = self._build_user_explanation(raw_row, feat, prob, risk)

        return {
            "prob": prob,
            "risk": risk,
            "explanation": explanation,
            "display": {
                "stop_id": raw_row.get("stop_id"),
                "stop_name": raw_row.get("stop_name", "Unknown station"),
                "line_id": raw_row.get("line_id"),
                "direction": raw_row.get("direction"),
                "platform_name": raw_row.get("platform_name", "Unknown platform"),
                "destination_name": raw_row.get("destination_name", "Unknown destination"),
            },
            "features": feat,
        }