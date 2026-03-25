from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = BASE_DIR / "app" / "artifacts"

BASELINE_TABLE_PATH = ARTIFACTS_DIR / "baseline_table.parquet"
MODEL_PATH = BASE_DIR / "app" / "models" / "lightgbm_v2_h300_balanced.joblib"

MODEL_FEATURES = [
    "hour",
    "weekday",
    "is_weekend",
    "time_to_station",
    "roll_mean_tts_10m",
    "roll_max_tts_10m",
    "roll_count_10m",
    "baseline_median_tts",
    "deviation_from_baseline",
]

MODEL_NAME = os.getenv("MODEL_NAME", "future_late_3min_300s")
ENABLE_INTELLIGENCE = os.getenv("ENABLE_INTELLIGENCE", "true").lower() == "true"
FORCE_MOCK_MODEL = os.getenv("FORCE_MOCK_MODEL", "false").lower() == "true"

ALERT_MODES = {
    "Conservative": {
        "alert_threshold": 0.80,
        "high_threshold": 0.80,
        "medium_threshold": 0.50,
    },
    "Balanced": {
        "alert_threshold": 0.60,
        "high_threshold": 0.70,
        "medium_threshold": 0.35,
    },
    "Sensitive": {
        "alert_threshold": 0.40,
        "high_threshold": 0.60,
        "medium_threshold": 0.25,
    },
}

DEFAULT_ALERT_MODE = os.getenv("DEFAULT_ALERT_MODE", "Balanced")