import os
import time
import sqlite3
from datetime import datetime, timedelta, timezone

import pandas as pd


# ----------------------------
# CONFIG (can be overridden via env)
# ----------------------------
DB_PATH = os.getenv("DB_PATH", "data/raw/tfl_arrivals_final_backup.sqlite")

# Dev window (hours). Start small for fast iteration: 6, 12, 24, 48...
DEV_HOURS = int(os.getenv("DEV_HOURS", "192"))

# Only these lines for this project
LINES = {"victoria", "jubilee"}

# Rolling window for Option B
ROLLING_WINDOW = os.getenv("ROLLING_WINDOW", "10min")

# Label threshold (seconds): late = deviation_from_baseline > threshold
LATE_THRESHOLD_SECONDS = int(os.getenv("LATE_THRESHOLD_SECONDS", "300"))  # 5 min

# Output paths
OUT_DATASET_PATH = os.getenv("OUT_DATASET_PATH", "data/processed/dataset_192H.parquet")
OUT_BASELINE_PATH = os.getenv("OUT_BASELINE_PATH", "data/processed/baseline_table_192H.parquet")

# Performance toggles
INCLUDE_ROLLING_STD = int(os.getenv("INCLUDE_ROLLING_STD", "0"))  # default OFF (std is expensive)
STOP_LIMIT = int(os.getenv("STOP_LIMIT", "0"))  # 0 = no limit; else limit to first N stops (dev speed)


def utc_now():
    return datetime.now(timezone.utc)


def main():
    os.makedirs("data/processed", exist_ok=True)

    t0 = time.time()

    def mark(msg: str):
        print(f"[{(time.time() - t0)/60:.2f} min] {msg}", flush=True)

    mark("Starting build_dataset.py")
    mark(f"DB_PATH={DB_PATH}")
    mark(f"DEV_HOURS={DEV_HOURS} | ROLLING_WINDOW={ROLLING_WINDOW} | LATE_THRESHOLD_SECONDS={LATE_THRESHOLD_SECONDS}")
    mark(f"INCLUDE_ROLLING_STD={INCLUDE_ROLLING_STD} | STOP_LIMIT={STOP_LIMIT}")

    # 1) Time cutoff
    cutoff_dt = utc_now() - timedelta(hours=DEV_HOURS)
    cutoff_iso = cutoff_dt.isoformat()
    mark(f"Cutoff: observed_at >= {cutoff_iso}")

    # 2) Load slice from SQLite (only necessary columns; drop raw_json)
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        observed_at,
        stop_id,
        stop_name,
        line_id,
        direction,
        platform_name,
        destination_name,
        time_to_station,
        expected_arrival,
        vehicle_id
    FROM raw_arrivals
    WHERE observed_at >= ?
      AND time_to_station IS NOT NULL
      AND line_id IS NOT NULL
    """

    df = pd.read_sql_query(query, conn, params=(cutoff_iso,))
    conn.close()

    if df.empty:
        raise RuntimeError("No data returned. Check DB_PATH, DEV_HOURS, or whether DB has data.")

    mark(f"Loaded rows (raw slice): {len(df):,}")

    # 3) Basic cleaning + filter to lines
    df["line_id"] = df["line_id"].astype(str).str.lower()
    df = df[df["line_id"].isin(LINES)].copy()
    mark(f"Rows after line filter {LINES}: {len(df):,}")

    # Some direction values can be None/odd; normalize
    df["direction"] = df["direction"].fillna("unknown").astype(str).str.lower()

    # Optional: limit number of stops for very fast dev runs
    if STOP_LIMIT > 0:
        keep_stops = df["stop_id"].dropna().astype(str).unique().tolist()[:STOP_LIMIT]
        df = df[df["stop_id"].isin(keep_stops)].copy()
        mark(f"Rows after STOP_LIMIT={STOP_LIMIT}: {len(df):,} (stops={len(keep_stops)})")

    # 4) Parse timestamps and types
    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")
    df["expected_arrival"] = pd.to_datetime(df["expected_arrival"], utc=True, errors="coerce")

    df["time_to_station"] = pd.to_numeric(df["time_to_station"], errors="coerce")

    df = df.dropna(subset=["observed_at", "stop_id", "time_to_station", "line_id"]).copy()
    mark(f"Rows after parsing/dropna: {len(df):,}")

    # 5) Time features
    df["hour"] = df["observed_at"].dt.hour
    df["weekday"] = df["observed_at"].dt.weekday  # Mon=0
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)

    # 6) Sort (KEEP a unique index; do NOT set observed_at as index)
    keys = ["stop_id", "line_id", "direction"]
    df = df.sort_values(keys + ["observed_at"]).reset_index(drop=True)
    mark("Sorted by keys + observed_at (kept RangeIndex)")

    # 7) Rolling features (position-based assignment; avoids duplicate-index alignment)
    mark("Computing rolling features (groupby().rolling(on=observed_at)) ...")

    keys = ["stop_id", "line_id", "direction"]

    roll = (
        df.groupby(keys, sort=False)
        .rolling(ROLLING_WINDOW, on="observed_at", closed="both")["time_to_station"]
    )

    if len(roll.mean()) != len(df):
        raise RuntimeError(f"Rolling result length {len(roll.mean())} != df length {len(df)} (unexpected)")

    # IMPORTANT: assign by position, not by index alignment
    df["roll_mean_tts_10m"] = roll.mean().to_numpy()
    df["roll_max_tts_10m"]  = roll.max().to_numpy()
    df["roll_count_10m"]    = roll.count().to_numpy()

    if INCLUDE_ROLLING_STD == 1:
        df["roll_std_tts_10m"] = roll.std().to_numpy()
    else:
        df["roll_std_tts_10m"] = pd.NA

    mark("Rolling features done")

    # 8) Baseline medians per bucket (stop,line,direction,hour,weekday)
    mark("Computing baseline median table ...")

    baseline = (
        df.groupby(["stop_id", "line_id", "direction", "hour", "weekday"], as_index=False)["time_to_station"]
        .median()
        .rename(columns={"time_to_station": "baseline_median_tts"})
    )

    mark(f"Baseline rows: {len(baseline):,}")

    # Join baseline
    df = df.merge(
        baseline,
        on=["stop_id", "line_id", "direction", "hour", "weekday"],
        how="left",
        validate="m:1",
    )

    # 9) Label
    df["deviation_from_baseline"] = df["time_to_station"] - df["baseline_median_tts"]
    df["late"] = (df["deviation_from_baseline"] > LATE_THRESHOLD_SECONDS).astype(int)

    # Drop rows missing baseline (rare with small slices)
    df = df.dropna(subset=["baseline_median_tts"]).copy()

    # 10) Final dataset columns
    keep_cols = [
        "observed_at",
        "stop_id",
        "stop_name",
        "line_id",
        "direction",
        "platform_name",
        "destination_name",
        "hour",
        "weekday",
        "is_weekend",
        "time_to_station",
        "roll_mean_tts_10m",
        "roll_max_tts_10m",
        "roll_count_10m",
        "roll_std_tts_10m",
        "baseline_median_tts",
        "deviation_from_baseline",
        "late",
    ]
    df_out = df[keep_cols].copy()

    mark("Dataset assembled")

    # 11) Print class balance
    late_counts = df_out["late"].value_counts(dropna=False)
    mark(f"late counts:\n{late_counts.to_string()}")

    mark(f"Final ML rows: {len(df_out):,}")

    # 12) Save outputs
    df_out.to_parquet(OUT_DATASET_PATH, index=False)
    baseline.to_parquet(OUT_BASELINE_PATH, index=False)

    mark(f"Saved ML dataset: {OUT_DATASET_PATH}")
    mark(f"Saved baseline table: {OUT_BASELINE_PATH}")
    mark("Done.")


if __name__ == "__main__":
    main()