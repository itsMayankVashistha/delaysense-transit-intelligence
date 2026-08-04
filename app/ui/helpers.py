"""Shared helpers for the DelaySense dashboard.

Support module for `streamlit_app.py`: asset loading, a cached HTTP client for
the backend, formatters, stable arrival identity and table construction.

No model or feature logic lives here. The dashboard remains a pure client of
the API and holds no scoring rules of its own.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

# --- Paths -----------------------------------------------------------------
# Resolved from __file__ so the app works regardless of the working directory
# it was launched from.
UI_DIR = Path(__file__).resolve().parent
ASSETS_DIR = UI_DIR / "assets"
CSS_PATH = UI_DIR / "theme.css"
HERO_PATH = ASSETS_DIR / "delaysense_banner_v2.webp"

API_URL = os.getenv("FRONTEND_API_URL", "http://localhost:8000").rstrip("/")

# London Underground runs on London time. Formatting against the network's own
# timezone keeps timestamps stable no matter where the app is hosted.
NETWORK_TZ = ZoneInfo("Europe/London")

# Chart colours only. Everything the browser paints lives in theme.css.
COLORS = {
    "text_main": "#14213D",
    "text_soft": "#667085",
    "high": "#E85D75",
    "medium": "#F6AE2D",
    "low": "#4CAF7D",
    "navy": "#23395B",
    "navy_light": "#7C93C3",
    "blue_soft": "#2563EB",
    "grid": "rgba(20,33,61,0.10)",
    "transparent": "rgba(255,255,255,0)",
}

RISK_ICONS = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢"}


# --- Assets ----------------------------------------------------------------


@st.cache_data(show_spinner=False)
def load_css() -> str:
    try:
        return CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


# --- API client ------------------------------------------------------------

WAKING_HINT = (
    "The backend runs on a free Render tier and may need up to a minute to "
    "wake from idle."
)


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, requests.Timeout):
        return f"The backend did not respond in time. {WAKING_HINT}"
    if isinstance(exc, requests.ConnectionError):
        return f"Could not reach the backend at {API_URL}. {WAKING_HINT}"
    if isinstance(exc, requests.HTTPError):
        status = getattr(exc.response, "status_code", "unknown")
        return f"The backend returned an error (HTTP {status})."
    return "The backend request failed unexpectedly."


def _request(method: str, path: str, timeout: int) -> Tuple[Optional[dict], Optional[str]]:
    """Return (payload, error). Never raises, so callers can render a state."""
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=timeout)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:  # noqa: BLE001 - surfaced as a UI state
        return None, _friendly_error(exc)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_health() -> Tuple[Optional[dict], Optional[str]]:
    return _request("GET", "/health", timeout=20)


@st.cache_data(ttl=20, show_spinner=False)
def fetch_live_monitoring() -> Tuple[Optional[dict], Optional[str]]:
    return _request("GET", "/monitor/live", timeout=30)


def refresh_live_monitoring() -> Tuple[Optional[dict], Optional[str]]:
    """Force a backend poll and drop the cached live payload."""
    payload, error = _request("POST", "/monitor/refresh", timeout=60)
    fetch_live_monitoring.clear()
    return payload, error


def active_alert_mode(health: Optional[dict]) -> Optional[str]:
    """The alert mode the backend is actually applying, when it reports one."""
    if not health:
        return None
    status = health.get("monitor_status") or {}
    mode = status.get("default_alert_mode")
    return str(mode) if mode else None


def format_model_name(model_info: Optional[dict]) -> str:
    if not model_info:
        return "ML model"
    name = model_info.get("model_name") or model_info.get("model_family") or ""
    lowered = str(name).lower()
    if "lightgbm" in lowered:
        return "LightGBM"
    if "xgboost" in lowered:
        return "XGBoost"
    if "logistic" in lowered:
        return "Logistic regression"
    if "randomforest" in lowered or "random_forest" in lowered:
        return "Random forest"
    return str(name) if name else "ML model"


# --- Formatting ------------------------------------------------------------


def format_seconds_human(seconds: Any) -> str:
    total = max(0, int(round(float(seconds))))
    if total < 60:
        return f"{total}s"
    mins, secs = divmod(total, 60)
    return f"{mins}m" if secs == 0 else f"{mins}m {secs}s"


def format_delta_human(delta_seconds: Any) -> str:
    delta = float(delta_seconds)
    if abs(delta) < 1:
        return "On time"
    if delta > 0:
        return f"{format_seconds_human(delta)} delay"
    return f"{format_seconds_human(abs(delta))} faster"


def format_network_time(value: Optional[str]) -> str:
    """Render an ISO timestamp in London time, independent of the host."""
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(NETWORK_TZ).strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return str(value)


def monitor_readiness_text(status: Optional[dict]) -> str:
    if not status:
        return "—"
    minutes = float(status.get("warmup_minutes", 0) or 0)
    state = str(status.get("warmup_status", "unknown")).lower()
    if state == "warm":
        return f"Ready ({minutes:.1f} min collected)"
    if state == "warming":
        return f"Collecting data ({minutes:.1f} / 10 min)"
    return "Starting up"


def overall_risk_label(avg_prob: float) -> str:
    if avg_prob >= 0.60:
        return "High"
    if avg_prob >= 0.30:
        return "Medium"
    return "Low"


def risk_tone(risk: Any) -> str:
    lowered = str(risk).lower()
    return lowered if lowered in {"high", "medium"} else "low"


def action_text_from_risk(risk: Any) -> str:
    lowered = str(risk).lower()
    if lowered == "high":
        return "Investigate immediately"
    if lowered == "medium":
        return "Monitor closely"
    return "No immediate action needed"


# --- Arrival identity ------------------------------------------------------


def assign_arrival_uids(results: List[dict]) -> List[dict]:
    """Attach a stable unique id to every arrival.

    Station names are not unique within a single poll, so selection keyed on
    the name silently collapsed duplicate stations. The id is derived from the
    arrival's own attributes, with an occurrence counter as a last resort, so
    it survives refreshes while still separating same-station arrivals.
    """
    seen: Dict[str, int] = {}
    for result in results:
        display = result.get("display") or {}
        base = "|".join(
            str(display.get(key) or "-")
            for key in ("stop_id", "line_id", "direction", "vehicle_id")
        )
        occurrence = seen.get(base, 0)
        seen[base] = occurrence + 1
        result["_uid"] = f"{base}#{occurrence}"
    return results


def find_arrival(results: List[dict], uid: Optional[str]) -> Optional[dict]:
    """Look up an arrival by id, falling back to the first available one."""
    if not results:
        return None
    for result in results:
        if result.get("_uid") == uid:
            return result
    return results[0]


def arrival_label(result: dict) -> str:
    display = result.get("display") or {}
    station = display.get("stop_name", "Unknown station")
    line = str(display.get("line_id") or "").title()
    direction = str(display.get("direction") or "").title()
    prob = float(result.get("prob", 0.0))
    parts = [part for part in (line, direction) if part]
    suffix = f" · {' '.join(parts)}" if parts else ""
    return f"{station}{suffix} — {prob:.0%}"


def strip_internal_keys(result: dict) -> dict:
    return {key: value for key, value in result.items() if not key.startswith("_")}


# --- Derived data ----------------------------------------------------------


def get_priority_results(results: List[dict], top_n: int = 3) -> List[dict]:
    return sorted(results, key=lambda r: float(r.get("prob", 0.0)), reverse=True)[:top_n]


def build_monitoring_table(results: List[dict]) -> pd.DataFrame:
    """Build the arrivals table with numeric columns so sorting is correct.

    Values stay numeric; presentation is handled by column_config.
    """
    rows = []
    for result in results:
        display = result.get("display") or {}
        features = result.get("features") or {}
        risk = str(result.get("risk", "low")).upper()

        current = float(features.get("time_to_station", 0) or 0)
        usual = float(features.get("baseline_median_tts", 0) or 0)
        deviation = float(features.get("deviation_from_baseline", 0) or 0)

        rows.append(
            {
                "_uid": result.get("_uid", ""),
                "Risk": f"{RISK_ICONS.get(risk, '⚪')} {risk.title()}",
                "Station": display.get("stop_name", "Unknown"),
                "Line": str(display.get("line_id") or "").title(),
                "Direction": str(display.get("direction") or "—").title(),
                "Destination": display.get("destination_name", "—"),
                "Delay risk": round(float(result.get("prob", 0.0)) * 100, 1),
                "Current": round(current / 60.0, 1),
                "Usual": round(usual / 60.0, 1),
                "Difference": round(deviation / 60.0, 1),
                "Alert": bool(result.get("alert_flag", False)),
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(
        by=["Delay risk", "Difference"], ascending=[False, False]
    ).reset_index(drop=True)


MONITOR_COLUMN_CONFIG = {
    "_uid": None,
    "Risk": st.column_config.TextColumn("Risk", width="small"),
    "Station": st.column_config.TextColumn("Station", width="medium"),
    "Line": st.column_config.TextColumn("Line", width="small"),
    "Direction": st.column_config.TextColumn("Direction", width="small"),
    "Destination": st.column_config.TextColumn("Destination", width="medium"),
    "Delay risk": st.column_config.ProgressColumn(
        "Delay risk (5 min)",
        help="Probability of a delay developing within the next five minutes",
        format="%.1f%%",
        min_value=0,
        max_value=100,
    ),
    "Current": st.column_config.NumberColumn(
        "Current", help="Current arrival estimate", format="%.1f min"
    ),
    "Usual": st.column_config.NumberColumn(
        "Usual", help="Baseline arrival estimate", format="%.1f min"
    ),
    "Difference": st.column_config.NumberColumn(
        "Difference", help="Deviation from baseline", format="%+.1f min"
    ),
    "Alert": st.column_config.CheckboxColumn("Alert", help="Above the alert threshold"),
}


def append_live_history(
    history: List[dict], results: List[dict], status: Optional[dict]
) -> List[dict]:
    """Append the current poll to the risk history.

    Deduplication is keyed on the arrival id rather than the station name, so
    several arrivals at the same station in one poll are all retained.
    """
    if not status:
        return history

    timestamp = status.get("last_success_at") or status.get("last_poll_at")
    if not timestamp:
        return history

    existing = {(item.get("timestamp"), item.get("uid")) for item in history}

    for result in results:
        uid = result.get("_uid")
        if (timestamp, uid) in existing:
            continue
        features = result.get("features") or {}
        history.append(
            {
                "timestamp": timestamp,
                "uid": uid,
                "station": (result.get("display") or {}).get("stop_name", "Unknown"),
                "prob": float(result.get("prob", 0.0)),
                "risk": str(result.get("risk", "low")).upper(),
            }
        )

    return history[-500:]


# --- Narrative -------------------------------------------------------------


def explanation_text(result: dict) -> str:
    features = result.get("features") or {}
    current = float(features.get("time_to_station", 0) or 0)
    usual = float(features.get("baseline_median_tts", 0) or 0)
    delta = float(features.get("deviation_from_baseline", 0) or 0)
    prob = float(result.get("prob", 0.0))
    risk = str(result.get("risk", "low")).lower()

    if delta > 0:
        state = (
            f"The current arrival estimate is {format_seconds_human(current)}, which is "
            f"{format_seconds_human(delta)} slower than the usual {format_seconds_human(usual)}."
        )
    elif delta < 0:
        state = (
            f"The current arrival estimate is {format_seconds_human(current)}, which is "
            f"{format_seconds_human(abs(delta))} faster than the usual {format_seconds_human(usual)}."
        )
    else:
        state = (
            f"The current arrival estimate is {format_seconds_human(current)}, in line with "
            f"the usual {format_seconds_human(usual)}."
        )

    if risk == "high":
        decision = f"This is a high-risk case ({prob:.1%}) and should be investigated immediately."
    elif risk == "medium":
        decision = f"This is a medium-risk case ({prob:.1%}) and should remain under close monitoring."
    else:
        decision = f"This is a low-risk case ({prob:.1%}) and does not currently require action."

    return f"{state} {decision}"


def action_sentence(result: dict) -> str:
    features = result.get("features") or {}
    display = result.get("display") or {}
    risk = str(result.get("risk", "low")).lower()
    station = display.get("stop_name", "This arrival")
    destination = display.get("destination_name", "its destination")
    delta = float(features.get("deviation_from_baseline", 0) or 0)

    if risk == "high":
        return (
            f"{station} is running significantly slower than usual and may create "
            f"downstream delay pressure toward {destination}."
        )
    if risk == "medium":
        return (
            f"{station} is showing elevated delay risk and should stay on the watchlist "
            "if conditions continue to worsen."
        )
    if delta < 0:
        return f"{station} is performing close to or slightly better than usual conditions."
    return f"{station} is operating near normal conditions with low near-term delay risk."


def arrival_history_frame(
    history: List[dict], uid: Optional[str], station: Optional[str]
) -> Optional[pd.DataFrame]:
    """Observation series for one arrival, in London time, or None if too short."""
    if not history:
        return None

    frame = pd.DataFrame(history)
    if frame.empty:
        return None

    if "uid" in frame.columns and uid is not None and (frame["uid"] == uid).any():
        frame = frame[frame["uid"] == uid].copy()
    elif "station" in frame.columns:
        frame = frame[frame["station"] == station].copy()
    else:
        return None

    if frame.empty:
        return None

    frame["ts"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame = frame.dropna(subset=["ts"]).sort_values("ts")
    if len(frame) < 2:
        return None

    frame["ts"] = frame["ts"].dt.tz_convert(NETWORK_TZ)
    return frame


def trend_summary(frame: pd.DataFrame, threshold: float) -> str:
    """One sentence describing how risk moved across the observed series."""
    first = float(frame["prob"].iloc[0])
    last = float(frame["prob"].iloc[-1])
    change = (last - first) * 100
    count = len(frame)

    if change >= 5:
        movement = f"risen {change:.0f} points"
    elif change <= -5:
        movement = f"fallen {abs(change):.0f} points"
    else:
        movement = "stayed broadly flat"

    position = "above" if last >= threshold else "below"
    return (
        f"Delay risk has {movement} across the last {count} observations and now sits "
        f"{last:.0%}, {position} the {threshold:.0%} alert threshold."
    )


def ranking_labels(results: List[dict]) -> List[str]:
    """Unique per-arrival labels, so same-station arrivals stay separate bars."""
    counts: Dict[str, int] = {}
    labels = []
    for result in results:
        display = result.get("display") or {}
        base = (
            f"{display.get('stop_name', 'Unknown')} · "
            f"{str(display.get('direction') or '—').title()}"
        )
        occurrence = counts.get(base, 0)
        counts[base] = occurrence + 1
        labels.append(base if occurrence == 0 else f"{base} ({occurrence + 1})")
    return labels


def micro_hint(features: dict) -> str:
    delta = float((features or {}).get("deviation_from_baseline", 0) or 0)
    if delta > 120:
        return "Currently slower than usual"
    if delta < -120:
        return "Currently faster than usual"
    return "Currently close to usual conditions"
