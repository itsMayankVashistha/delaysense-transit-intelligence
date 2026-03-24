import pandas as pd
from pathlib import Path


class BaselineService:
    def __init__(self, path):
        self.path = Path(path)

        if not self.path.exists():
            raise FileNotFoundError(
                f"Baseline parquet not found: {self.path}"
            )

        self.df = pd.read_parquet(self.path)

    def lookup(self, stop_id, line_id, direction, hour, weekday):
        df = self.df

        row = df[
            (df["stop_id"] == stop_id)
            & (df["line_id"] == line_id)
            & (df["direction"] == direction)
            & (df["hour"] == hour)
            & (df["weekday"] == weekday)
        ]

        if not row.empty:
            return float(row["baseline_median_tts"].iloc[0])

        row = df[
            (df["stop_id"] == stop_id)
            & (df["line_id"] == line_id)
            & (df["direction"] == direction)
            & (df["hour"] == hour)
        ]
        if not row.empty:
            return float(row["baseline_median_tts"].median())

        row = df[
            (df["stop_id"] == stop_id)
            & (df["line_id"] == line_id)
            & (df["direction"] == direction)
        ]
        if not row.empty:
            return float(row["baseline_median_tts"].median())

        row = df[df["line_id"] == line_id]
        if not row.empty:
            return float(row["baseline_median_tts"].median())

        return 300.0