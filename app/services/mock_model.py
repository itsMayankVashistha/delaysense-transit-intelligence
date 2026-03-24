import math


class MockModel:
    def predict_proba(self, X):
        results = []

        for row in X:
            # expected order:
            # hour, weekday, is_weekend, time_to_station,
            # roll_mean_tts_10m, roll_max_tts_10m, roll_count_10m,
            # baseline_median_tts, deviation_from_baseline

            hour = row[0]
            time_to_station = row[3]
            roll_mean = row[4]
            roll_max = row[5]
            roll_count = row[6]
            baseline = row[7]
            deviation = row[8]

            score = 0.0

            if baseline > 0:
                score += deviation / baseline

            if roll_mean > baseline:
                score += 0.5

            if roll_max > baseline * 1.3:
                score += 0.4

            if roll_count >= 3:
                score += 0.2

            if 7 <= hour <= 9 or 16 <= hour <= 19:
                score += 0.15

            prob = 1 / (1 + math.exp(-score))
            prob = max(0.02, min(0.98, prob))

            results.append([1 - prob, prob])

        return results