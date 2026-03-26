from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import time

import requests


DEFAULT_MONITORED_STOPS = {
    "940GZZLUOXC": "Oxford Circus",
    "940GZZLUGPK": "Green Park",
    "940GZZLUBXN": "Brixton",
    "940GZZLUWLO": "Waterloo",
    "940GZZLUSTD": "Stratford",
}


@dataclass
class TfLApiService:
    app_id: Optional[str] = None
    app_key: Optional[str] = None
    timeout_seconds: int = 12

    BASE_URL = "https://api.tfl.gov.uk"

    def _build_url(self, stop_id: str) -> str:
        return f"{self.BASE_URL}/StopPoint/{stop_id}/Arrivals"

    def _build_params(self) -> Dict[str, str]:
        params: Dict[str, str] = {}
        if self.app_id:
            params["app_id"] = self.app_id
        if self.app_key:
            params["app_key"] = self.app_key
        return params

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _normalize_arrival(self, item: Dict[str, Any], fallback_stop_id: str) -> Optional[Dict[str, Any]]:
        line_id = (item.get("lineId") or "").lower()
        if line_id not in {"victoria", "jubilee"}:
            return None

        time_to_station = self._safe_float(item.get("timeToStation"), default=-1)
        if time_to_station < 0:
            return None

        stop_id = item.get("naptanId") or fallback_stop_id
        stop_name = item.get("stationName") or DEFAULT_MONITORED_STOPS.get(stop_id) or "Unknown station"

        direction = (item.get("direction") or "unknown").lower()
        platform_name = item.get("platformName") or "Unknown platform"
        destination_name = item.get("destinationName") or "Unknown destination"

        vehicle_id = (
            item.get("vehicleId")
            or item.get("id")
            or f"live_{stop_id}_{line_id}_{destination_name}"
        )

        observed_at_ms = int(time.time() * 1000)

        return {
            "observed_at": observed_at_ms,
            "stop_id": stop_id,
            "stop_name": stop_name,
            "line_id": line_id,
            "vehicle_id": str(vehicle_id),
            "direction": direction,
            "platform_name": platform_name,
            "destination_name": destination_name,
            "time_to_station": time_to_station,
        }

    def fetch_arrivals_for_stop(self, stop_id: str) -> List[Dict[str, Any]]:
        url = self._build_url(stop_id)
        response = requests.get(
            url,
            params=self._build_params(),
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for item in data:
            row = self._normalize_arrival(item, fallback_stop_id=stop_id)
            if row is not None:
                normalized.append(row)

        normalized.sort(key=lambda x: x["time_to_station"])
        return normalized

    def fetch_arrivals_for_stops(
        self,
        stop_ids: List[str],
        max_per_stop: int = 5,
    ) -> List[Dict[str, Any]]:
        all_rows: List[Dict[str, Any]] = []

        for stop_id in stop_ids:
            try:
                arrivals = self.fetch_arrivals_for_stop(stop_id)
                if max_per_stop is not None and max_per_stop > 0:
                    arrivals = arrivals[:max_per_stop]
                all_rows.extend(arrivals)
            except requests.RequestException as e:
                print(f"Warning: failed to fetch TfL arrivals for {stop_id}: {e}")

        all_rows.sort(key=lambda x: x["time_to_station"])
        return all_rows

    def fetch_demo_monitored_arrivals(
        self,
        stop_ids: Optional[List[str]] = None,
        max_per_stop: int = 3,
    ) -> List[Dict[str, Any]]:
        stop_ids = stop_ids or list(DEFAULT_MONITORED_STOPS.keys())
        return self.fetch_arrivals_for_stops(stop_ids=stop_ids, max_per_stop=max_per_stop)