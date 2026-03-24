from datetime import datetime


class FeaturePipeline:
    def __init__(self, baseline_service, rolling_cache):
        self.baseline = baseline_service
        self.cache = rolling_cache

    def _build_cache_key(self, row):
        return (
            row.get("vehicle_id", "unknown_vehicle"),
            row.get("stop_id", "unknown_stop"),
            row.get("direction", "unknown_direction"),
            row.get("destination_name", "unknown_destination"),
        )

    def build(self, row):
        stop_id = row["stop_id"]
        line_id = row["line_id"]
        direction = row["direction"]
        vehicle_id = row.get("vehicle_id")
        destination_name = row.get("destination_name", "Unknown destination")

        tts = float(row["time_to_station"])

        now = datetime.fromtimestamp(row["observed_at"] / 1000)
        hour = now.hour
        weekday = now.weekday()
        is_weekend = int(weekday >= 5)

        key = self._build_cache_key(row)

        self.cache.add(key, now, tts)
        roll_mean, roll_max, roll_count = self.cache.get_stats(key)

        baseline = self.baseline.lookup(
            stop_id=stop_id,
            line_id=line_id,
            direction=direction,
            hour=hour,
            weekday=weekday,
        )

        deviation_from_baseline = tts - baseline

        model_features = {
            "hour": hour,
            "weekday": weekday,
            "is_weekend": is_weekend,
            "time_to_station": tts,
            "roll_mean_tts_10m": roll_mean,
            "roll_max_tts_10m": roll_max,
            "roll_count_10m": roll_count,
            "baseline_median_tts": baseline,
            "deviation_from_baseline": deviation_from_baseline,
        }

        context = {
            "stop_id": stop_id,
            "stop_name": row.get("stop_name", "Unknown station"),
            "line_id": line_id,
            "direction": direction,
            "platform_name": row.get("platform_name", "Unknown platform"),
            "destination_name": destination_name,
            "vehicle_id": vehicle_id,
            "observed_at": row["observed_at"],
        }

        return {
            "model_features": model_features,
            "context": context,
        }