from datetime import datetime


class FeaturePipeline:

    def __init__(
        self,
        baseline_service,
        rolling_cache,
    ):

        self.baseline = baseline_service
        self.cache = rolling_cache

    def build(self, row):

        stop_id = row["stop_id"]
        line_id = row["line_id"]
        direction = row["direction"]

        tts = row["time_to_station"]

        now = datetime.fromtimestamp(
            row["observed_at"] / 1000
        )

        hour = now.hour
        weekday = now.weekday()

        key = (stop_id, line_id, direction)

        self.cache.add(key, now, tts)

        roll_mean, roll_max, roll_count = (
            self.cache.get_stats(key)
        )

        baseline = self.baseline.lookup(
            stop_id,
            line_id,
            direction,
            hour,
            weekday,
        )

        return {

            "time_to_station": tts,

            "roll_mean_tts_10m": roll_mean,
            "roll_max_tts_10m": roll_max,
            "roll_count_10m": roll_count,

            "baseline_median_tts": baseline,

            "hour": hour,
            "weekday": weekday,
            "is_weekend": int(weekday >= 5),

            "stop_id": stop_id,
            "line_id": line_id,
            "direction": direction,

        }