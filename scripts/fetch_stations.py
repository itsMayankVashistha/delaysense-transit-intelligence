import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

BASE_URL = "https://api.tfl.gov.uk"

def get_json(url: str, params: dict) -> dict:
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    load_dotenv()
    app_key = os.getenv("TFL_APP_KEY")
    if not app_key:
        raise ValueError("Missing TFL_APP_KEY in .env")

    # ✅ Choose two tube lines (edit if you want)
    lines = ["victoria", "jubilee"]

    all_rows = []
    for line in lines:
        url = f"{BASE_URL}/Line/{line}/StopPoints"
        data = get_json(url, params={"app_key": app_key})
        # data is a list of StopPoint objects
        for sp in data:
            all_rows.append({
                "stop_id": sp.get("naptanId") or sp.get("id"),
                "stop_name": sp.get("commonName"),
                "line": line,
                "modes": ",".join(sp.get("modes", [])) if isinstance(sp.get("modes"), list) else sp.get("modes"),
                "lat": sp.get("lat"),
                "lon": sp.get("lon"),
            })
        time.sleep(0.2)

    df = pd.DataFrame(all_rows).dropna(subset=["stop_id"]).drop_duplicates(["stop_id", "line"])
    out_path = "data/raw/stations.csv"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Saved {len(df)} rows to {out_path}")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()