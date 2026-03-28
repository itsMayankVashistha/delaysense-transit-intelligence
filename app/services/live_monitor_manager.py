from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Event, Lock, Thread
from typing import Any, Dict, List, Optional
import time


@dataclass
class LiveMonitorManager:
    tfl_api_service: Any
    inference_service: Any
    monitored_stop_ids: List[str]
    poll_interval_seconds: int = 30
    max_per_stop: int = 3
    default_alert_mode: str = "Balanced"
    include_intelligence: bool = False

    _thread: Optional[Thread] = field(default=None, init=False)
    _stop_event: Event = field(default_factory=Event, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    _is_running: bool = field(default=False, init=False)
    _last_poll_ts: Optional[float] = field(default=None, init=False)
    _last_success_ts: Optional[float] = field(default=None, init=False)
    _last_error: Optional[str] = field(default=None, init=False)
    _latest_results: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _latest_raw_rows: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _started_at_ts: Optional[float] = field(default=None, init=False)
    _poll_count: int = field(default=0, init=False)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._started_at_ts = time.time()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        self._is_running = True
        try:
            while not self._stop_event.is_set():
                self.poll_once()
                self._stop_event.wait(self.poll_interval_seconds)
        finally:
            self._is_running = False

    def poll_once(self) -> None:
        self._last_poll_ts = time.time()
        try:
            rows = self.tfl_api_service.fetch_arrivals_for_stops(
                stop_ids=self.monitored_stop_ids,
                max_per_stop=self.max_per_stop,
            )

            predictions = []
            for row in rows:
                pred = self.inference_service.predict(
                    row,
                    alert_mode=self.default_alert_mode,
                    include_intelligence=self.include_intelligence,
                )
                predictions.append(pred)

            predictions = sorted(
                predictions,
                key=lambda x: (float(x.get("prob", 0.0)), float(x.get("features", {}).get("deviation_from_baseline", 0.0))),
                reverse=True,
            )

            with self._lock:
                self._latest_raw_rows = rows
                self._latest_results = predictions
                self._last_success_ts = time.time()
                self._last_error = None
                self._poll_count += 1

        except Exception as e:
            with self._lock:
                self._last_error = str(e)

    def get_latest_results(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._latest_results)

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            started_at_ts = self._started_at_ts
            last_poll_ts = self._last_poll_ts
            last_success_ts = self._last_success_ts
            warmup_seconds = 0.0
            if started_at_ts is not None:
                warmup_seconds = max(0.0, time.time() - started_at_ts)

            return {
                "is_running": self._is_running,
                "poll_interval_seconds": self.poll_interval_seconds,
                "max_per_stop": self.max_per_stop,
                "default_alert_mode": self.default_alert_mode,
                "include_intelligence": self.include_intelligence,
                "monitored_stop_ids": self.monitored_stop_ids,
                "started_at": self._fmt_ts(started_at_ts),
                "last_poll_at": self._fmt_ts(last_poll_ts),
                "last_success_at": self._fmt_ts(last_success_ts),
                "warmup_seconds": round(warmup_seconds, 1),
                "warmup_minutes": round(warmup_seconds / 60.0, 2),
                "warmup_status": self._warmup_status(warmup_seconds),
                "latest_result_count": len(self._latest_results),
                "latest_raw_row_count": len(self._latest_raw_rows),
                "poll_count": self._poll_count,
                "last_error": self._last_error,
            }

    def _warmup_status(self, warmup_seconds: float) -> str:
        if warmup_seconds >= 600:
            return "warm"
        if warmup_seconds >= 180:
            return "warming"
        return "cold"

    @staticmethod
    def _fmt_ts(ts: Optional[float]) -> Optional[str]:
        if ts is None:
            return None
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()