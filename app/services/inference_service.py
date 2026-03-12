class InferenceService:

    def __init__(
        self,
        model,
        pipeline,
    ):

        self.model = model
        self.pipeline = pipeline

    def predict(self, raw_row):

        feat = self.pipeline.build(raw_row)

        prob = self.model.predict_proba(
            [feat]
        )[0][1]

        if prob > 0.7:
            risk = "high"
        elif prob > 0.3:
            risk = "medium"
        else:
            risk = "low"

        return {

            "prob": prob,
            "risk": risk,
            "features": feat,
        }