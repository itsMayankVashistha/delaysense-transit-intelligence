from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

ARTIFACTS_DIR = BASE_DIR / "app" / "artifacts"

BASELINE_TABLE_PATH = ARTIFACTS_DIR / "baseline_table.parquet"
MODEL_PATH = ARTIFACTS_DIR / "model.joblib"