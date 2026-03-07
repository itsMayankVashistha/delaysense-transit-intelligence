import os
import time
import json
import sqlite3
from datetime import datetime, timezone

import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

BASE_URL = "https://api.tfl.gov.uk"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_arrivals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at TEXT NOT NULL,
    stop_id TEXT NOT NULL,
    stop_name TEXT,
    line_id TEXT,
    direction TEXT,
    platform_name TEXT,
    destination_name TEXT,
    time_to_station INTEGER,
    expected_arrival TEXT,
    vehicle_id TEXT,
    raw_json TEXT
);
"""

INSERT_SQL = """
INSERT INTO raw_arrivals (
    observed_at, stop_id, stop_name, line_id, direction, platform_name,
    destination_name, time_to_station, expected_arrival, vehicle_id, raw_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_arrivals(stop_id: str, app_key: str):
    url = f"{BASE_URL}/StopPoint/{stop_id}/Arrivals"
    r = requests.get(url, params={"app_key": app_key}, timeout=30)
    r.raise_for_status()
    return r.json()  # list

def main():
    load_dotenv()
    app_key = os.getenv("TFL_APP_KEY")
    db_path = os.getenv("DB_PATH", "data/raw/tfl_arrivals.sqlite")
    poll_seconds = int(os.getenv("POLL_SECONDS", "60"))

    if not app_key:
        raise ValueError("Missing TFL_APP_KEY in .env")

    stations_path = "data/raw/stations.csv"
    if not os.path.exists(stations_path):
        raise FileNotFoundError(f"{stations_path} not found. Run fetch_stations.py first.")

    stations = pd.read_csv(stations_path)
    stop_ids = stations["stop_id"].dropna().astype(str).unique().tolist()

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()

    print(f"Collecting arrivals for {len(stop_ids)} stops every {poll_seconds}s")
    print(f"DB: {db_path}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            observed_at = utc_now_iso()
            rows_to_insert = []

            for stop_id in tqdm(stop_ids, desc="Stops", leave=False):
                try:
                    arrivals = get_arrivals(stop_id, app_key)
                except Exception as e:
                    # skip but keep going
                    continue

                for a in arrivals:
                    rows_to_insert.append((
                        observed_at,
                        stop_id,
                        a.get("stationName") or a.get("commonName"),
                        a.get("lineId"),
                        a.get("direction"),
                        a.get("platformName"),
                        a.get("destinationName"),
                        a.get("timeToStation"),
                        a.get("expectedArrival"),
                        a.get("vehicleId"),
                        json.dumps(a, ensure_ascii=False),
                    ))

                time.sleep(0.05)  # be gentle to API

            if rows_to_insert:
                cur.executemany(INSERT_SQL, rows_to_insert)
                conn.commit()

            print(f"[{observed_at}] inserted {len(rows_to_insert)} rows")
            time.sleep(poll_seconds)

    except KeyboardInterrupt:
        print("Stopping collector...")

    finally:
        conn.close()

if __name__ == "__main__":
    main()