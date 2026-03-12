import pandas as pd


class BaselineService:

    def __init__(self, path):

        self.df = pd.read_parquet(path)

    def lookup(
        self,
        stop_id,
        line_id,
        direction,
        hour,
        weekday,
    ):

        df = self.df

        row = df[
            (df["stop_id"] == stop_id)
            & (df["line_id"] == line_id)
            & (df["direction"] == direction)
            & (df["hour"] == hour)
            & (df["weekday"] == weekday)
        ]

        if len(row) > 0:
            return float(row["baseline_median_tts"].iloc[0])

        # fallback

        row = df[
            (df["line_id"] == line_id)
        ]

        if len(row) > 0:
            return float(row["baseline_median_tts"].median())

        return 300.0