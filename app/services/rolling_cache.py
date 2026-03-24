from collections import defaultdict
from datetime import datetime, timedelta


class RollingCache:

    def __init__(self, window_minutes=10):

        self.window = timedelta(minutes=window_minutes)

        self.store = defaultdict(list)

    def add(
        self,
        key,
        time,
        tts,
    ):

        self.store[key].append((time, tts))

        self._cleanup(key, time)

    def _cleanup(self, key, now):

        limit = now - self.window

        self.store[key] = [
            (t, v)
            for (t, v) in self.store[key]
            if t >= limit
        ]

    def get_stats(self, key):

        values = [v for _, v in self.store[key]]

        if not values:
            return 0, 0, 0

        return (
            sum(values) / len(values),
            max(values),
            len(values),
        )