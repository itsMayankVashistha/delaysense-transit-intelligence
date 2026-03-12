class MockModel:

    def predict_proba(self, X):

        probs = []

        for row in X:

            tts = row["time_to_station"]
            base = row["baseline_median_tts"]

            diff = tts - base

            p = min(max(diff / 600, 0), 1)

            probs.append([1 - p, p])

        return probs