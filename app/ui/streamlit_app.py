from pathlib import Path
from datetime import datetime
import base64
import json

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = "http://localhost:8000"
HERO_IMAGE = Path("app/ui/assets/banner1.png")

COLORS = {
    "bg_top_left": "rgba(124,147,195,0.10)",
    "bg_top_right": "rgba(232,93,117,0.08)",
    "bg_start": "#f7f9fc",
    "bg_end": "#eef3f9",
    "text_main": "#14213D",
    "text_soft": "#667085",
    "panel_border": "rgba(214,223,235,0.78)",
    "panel_bg": "rgba(255,255,255,0.93)",
    "high": "#E85D75",
    "high_dark": "#D94B64",
    "medium": "#F6AE2D",
    "medium_dark": "#E39115",
    "low": "#4CAF7D",
    "low_dark": "#2F8F68",
    "navy": "#23395B",
    "navy_light": "#7C93C3",
    "blue_soft": "#4F7DF3",
    "blue_bg": "rgba(79,125,243,0.10)",
    "green_bg": "rgba(76,175,125,0.12)",
    "amber_bg": "rgba(246,174,45,0.14)",
    "red_bg": "rgba(232,93,117,0.12)",
    "plot_bg": "rgba(255,255,255,0)",
}

st.set_page_config(
    page_title="DelaySense",
    page_icon="🚇",
    layout="wide",
)

st.markdown(
    f"""
    <style>
    .stApp {{
        background:
            radial-gradient(circle at top left, {COLORS["bg_top_left"]}, transparent 28%),
            radial-gradient(circle at top right, {COLORS["bg_top_right"]}, transparent 25%),
            linear-gradient(180deg, {COLORS["bg_start"]} 0%, {COLORS["bg_end"]} 100%);
    }}

    .block-container {{
        padding-top: 1.05rem;
        padding-bottom: 2rem;
        max-width: 1480px;
    }}

    .panel {{
        background: {COLORS["panel_bg"]};
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 1.08rem 1.08rem 1.02rem 1.08rem;
        box-shadow: 0 14px 32px rgba(20,33,61,0.08);
        border: 1px solid {COLORS["panel_border"]};
        margin-bottom: 1rem;
    }}

    .section-title {{
        font-size: 1.12rem;
        font-weight: 800;
        color: {COLORS["text_main"]};
        margin-bottom: 0.75rem;
    }}

    .hero-banner {{
        position: relative;
        min-height: 268px;
        border-radius: 30px;
        overflow: hidden;
        margin-bottom: 1.15rem;
        background-size: cover;
        background-position: center center;
        box-shadow: 0 20px 44px rgba(20,33,61,0.15);
        border: 1px solid rgba(255,255,255,0.35);
    }}

    .hero-banner::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(
            90deg,
            rgba(20,33,61,0.88) 0%,
            rgba(20,33,61,0.66) 36%,
            rgba(20,33,61,0.24) 66%,
            rgba(20,33,61,0.08) 100%
        );
    }}

    .hero-content {{
        position: relative;
        z-index: 2;
        padding: 1.9rem 2.05rem;
        max-width: 780px;
    }}

    .hero-title-overlay {{
        font-size: 2.45rem;
        font-weight: 900;
        color: white;
        line-height: 1.02;
        margin-bottom: 0.55rem;
    }}

    .hero-sub-overlay {{
        color: rgba(255,255,255,0.90);
        font-size: 1rem;
        line-height: 1.5;
        margin-bottom: 0.22rem;
    }}

    .hero-tag-row {{
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }}

    .hero-tag {{
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.22);
        color: white;
        padding: 0.44rem 0.78rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
    }}

    .status-card {{
        border-radius: 20px;
        padding: 1rem;
        border: 1px solid {COLORS["panel_border"]};
        min-height: 132px;
        box-shadow: 0 10px 24px rgba(20,33,61,0.06);
        background: white;
    }}

    .status-card.blue {{
        background: linear-gradient(180deg, rgba(79,125,243,0.10), rgba(255,255,255,0.98));
    }}

    .status-card.green {{
        background: linear-gradient(180deg, rgba(76,175,125,0.11), rgba(255,255,255,0.98));
    }}

    .status-card.amber {{
        background: linear-gradient(180deg, rgba(246,174,45,0.12), rgba(255,255,255,0.98));
    }}

    .status-card.red {{
        background: linear-gradient(180deg, rgba(232,93,117,0.10), rgba(255,255,255,0.98));
    }}

    .status-label {{
        font-size: 0.9rem;
        color: {COLORS["text_soft"]};
        margin-bottom: 0.22rem;
    }}

    .status-value {{
        font-size: 1.95rem;
        font-weight: 900;
        color: {COLORS["text_main"]};
        line-height: 1.05;
    }}

    .status-sub {{
        margin-top: 0.35rem;
        font-size: 0.85rem;
        color: {COLORS["text_soft"]};
    }}

    .summary-chip {{
        background: white;
        border-radius: 18px;
        padding: 0.95rem 1rem;
        border: 1px solid {COLORS["panel_border"]};
        box-shadow: 0 8px 20px rgba(20,33,61,0.05);
        min-height: 110px;
    }}

    .summary-chip-label {{
        font-size: 0.85rem;
        color: {COLORS["text_soft"]};
        margin-bottom: 0.2rem;
    }}

    .summary-chip-value {{
        font-size: 1.42rem;
        font-weight: 900;
        color: {COLORS["text_main"]};
        line-height: 1.08;
    }}

    .summary-chip-sub {{
        margin-top: 0.35rem;
        font-size: 0.82rem;
        color: {COLORS["text_soft"]};
    }}

    .risk-banner {{
        border-radius: 24px;
        padding: 1.15rem 1.3rem;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 14px 30px rgba(20,33,61,0.12);
    }}

    .risk-banner.high {{
        background: linear-gradient(135deg, {COLORS["high_dark"]}, {COLORS["high"]});
    }}

    .risk-banner.medium {{
        background: linear-gradient(135deg, {COLORS["medium_dark"]}, {COLORS["medium"]});
    }}

    .risk-banner.low {{
        background: linear-gradient(135deg, {COLORS["low_dark"]}, {COLORS["low"]});
    }}

    .inspect-card {{
        background: white;
        border: 1px solid {COLORS["panel_border"]};
        border-radius: 22px;
        padding: 1rem;
        box-shadow: 0 10px 22px rgba(20,33,61,0.05);
    }}

    .explanation-box {{
        background: rgba(255,255,255,0.95);
        border: 1px solid {COLORS["panel_border"]};
        border-radius: 18px;
        padding: 1rem 1.08rem;
        color: {COLORS["text_main"]};
        line-height: 1.68;
    }}

    .kpi-row {{
        display: flex;
        gap: 0.85rem;
        flex-wrap: wrap;
        margin-top: 0.18rem;
    }}

    .kpi-pill {{
        background: rgba(255,255,255,0.96);
        border: 1px solid rgba(220,227,238,0.95);
        border-radius: 18px;
        padding: 0.88rem 1rem;
        min-width: 180px;
        box-shadow: 0 8px 18px rgba(20,33,61,0.04);
    }}

    .kpi-pill-label {{
        font-size: 0.78rem;
        color: {COLORS["text_soft"]};
        margin-bottom: 0.2rem;
    }}

    .kpi-pill-value {{
        font-size: 1.12rem;
        font-weight: 900;
        color: {COLORS["text_main"]};
    }}

    .muted {{
        color: {COLORS["text_soft"]};
    }}

    div[data-testid="stDataFrame"] {{
        border-radius: 18px;
        overflow: hidden;
    }}

    .empty-state {{
        padding: 2.8rem 1rem;
        text-align: center;
        color: {COLORS["text_soft"]};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def build_showcase_demo_payload():
    results = [
        {
            "prob": 0.91,
            "risk": "high",
            "alert_flag": True,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 11m 20s, which is 5m 10s slower than the usual 6m 10s. The system flags this as high delay risk.",
            "display": {
                "stop_id": "940GZZLUOXC",
                "stop_name": "Oxford Circus Underground Station",
                "line_id": "victoria",
                "direction": "outbound",
                "platform_name": "Northbound - Platform 6",
                "destination_name": "Walthamstow Central Underground Station",
                "vehicle_id": "showcase_001",
                "observed_at": 1772357400000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 680,
                "roll_mean_tts_10m": 640,
                "roll_max_tts_10m": 720,
                "roll_count_10m": 8,
                "baseline_median_tts": 370,
                "deviation_from_baseline": 310,
            },
        },
        {
            "prob": 0.84,
            "risk": "high",
            "alert_flag": True,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 9m 45s, which is 4m 5s slower than the usual 5m 40s. The system flags this as high delay risk.",
            "display": {
                "stop_id": "940GZZLUWLO",
                "stop_name": "Waterloo Underground Station",
                "line_id": "jubilee",
                "direction": "outbound",
                "platform_name": "Outbound Platform",
                "destination_name": "Stratford Underground Station",
                "vehicle_id": "showcase_002",
                "observed_at": 1772357460000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 585,
                "roll_mean_tts_10m": 560,
                "roll_max_tts_10m": 620,
                "roll_count_10m": 7,
                "baseline_median_tts": 340,
                "deviation_from_baseline": 245,
            },
        },
        {
            "prob": 0.73,
            "risk": "high",
            "alert_flag": True,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 8m 15s, which is 3m 20s slower than the usual 4m 55s. The system flags this as high delay risk.",
            "display": {
                "stop_id": "940GZZLUGPK",
                "stop_name": "Green Park Underground Station",
                "line_id": "victoria",
                "direction": "inbound",
                "platform_name": "Southbound Platform",
                "destination_name": "Brixton Underground Station",
                "vehicle_id": "showcase_003",
                "observed_at": 1772357520000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 495,
                "roll_mean_tts_10m": 460,
                "roll_max_tts_10m": 520,
                "roll_count_10m": 7,
                "baseline_median_tts": 295,
                "deviation_from_baseline": 200,
            },
        },
        {
            "prob": 0.52,
            "risk": "medium",
            "alert_flag": False,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 6m 40s, which is 1m 55s slower than the usual 4m 45s. The system detects elevated delay risk.",
            "display": {
                "stop_id": "940GZZLUSTD",
                "stop_name": "Stratford Underground Station",
                "line_id": "jubilee",
                "direction": "inbound",
                "platform_name": "Inbound Platform",
                "destination_name": "Stanmore Underground Station",
                "vehicle_id": "showcase_004",
                "observed_at": 1772357580000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 400,
                "roll_mean_tts_10m": 380,
                "roll_max_tts_10m": 450,
                "roll_count_10m": 6,
                "baseline_median_tts": 285,
                "deviation_from_baseline": 115,
            },
        },
        {
            "prob": 0.44,
            "risk": "medium",
            "alert_flag": False,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 5m 30s, which is 1m 25s slower than the usual 4m 5s. The system detects elevated delay risk.",
            "display": {
                "stop_id": "940GZZLUWLO",
                "stop_name": "Waterloo Underground Station",
                "line_id": "jubilee",
                "direction": "inbound",
                "platform_name": "Inbound Platform",
                "destination_name": "Stanmore Underground Station",
                "vehicle_id": "showcase_005",
                "observed_at": 1772357640000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 330,
                "roll_mean_tts_10m": 310,
                "roll_max_tts_10m": 360,
                "roll_count_10m": 6,
                "baseline_median_tts": 245,
                "deviation_from_baseline": 85,
            },
        },
        {
            "prob": 0.36,
            "risk": "medium",
            "alert_flag": False,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 4m 50s, which is 1m 10s slower than the usual 3m 40s. The system detects elevated delay risk.",
            "display": {
                "stop_id": "940GZZLUBXN",
                "stop_name": "Brixton Underground Station",
                "line_id": "victoria",
                "direction": "outbound",
                "platform_name": "Northbound Platform",
                "destination_name": "Walthamstow Central Underground Station",
                "vehicle_id": "showcase_006",
                "observed_at": 1772357700000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 290,
                "roll_mean_tts_10m": 275,
                "roll_max_tts_10m": 320,
                "roll_count_10m": 6,
                "baseline_median_tts": 220,
                "deviation_from_baseline": 70,
            },
        },
        {
            "prob": 0.18,
            "risk": "low",
            "alert_flag": False,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 4m 2s, which is close to the usual 4m 10s. The system considers delay risk low.",
            "display": {
                "stop_id": "940GZZLUOXC",
                "stop_name": "Oxford Circus Underground Station",
                "line_id": "victoria",
                "direction": "inbound",
                "platform_name": "Southbound Platform",
                "destination_name": "Brixton Underground Station",
                "vehicle_id": "showcase_007",
                "observed_at": 1772357760000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 242,
                "roll_mean_tts_10m": 250,
                "roll_max_tts_10m": 285,
                "roll_count_10m": 5,
                "baseline_median_tts": 250,
                "deviation_from_baseline": -8,
            },
        },
        {
            "prob": 0.11,
            "risk": "low",
            "alert_flag": False,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 3m 20s, which is 20s faster than the usual 3m 40s. The system considers delay risk low.",
            "display": {
                "stop_id": "940GZZLUGPK",
                "stop_name": "Green Park Underground Station",
                "line_id": "victoria",
                "direction": "outbound",
                "platform_name": "Northbound Platform",
                "destination_name": "Walthamstow Central Underground Station",
                "vehicle_id": "showcase_008",
                "observed_at": 1772357820000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 200,
                "roll_mean_tts_10m": 205,
                "roll_max_tts_10m": 240,
                "roll_count_10m": 5,
                "baseline_median_tts": 220,
                "deviation_from_baseline": -20,
            },
        },
        {
            "prob": 0.06,
            "risk": "low",
            "alert_flag": False,
            "alert_mode": "Balanced",
            "alert_threshold": 0.60,
            "model_source": "showcase_demo",
            "model_info": {"model_name": "lightgbm_v2"},
            "explanation": "Current arrival estimate is 2m 35s, which is 35s faster than the usual 3m 10s. The system considers delay risk low.",
            "display": {
                "stop_id": "940GZZLUSTD",
                "stop_name": "Stratford Underground Station",
                "line_id": "jubilee",
                "direction": "outbound",
                "platform_name": "Outbound Platform",
                "destination_name": "Stratford Underground Station",
                "vehicle_id": "showcase_009",
                "observed_at": 1772357880000,
            },
            "features": {
                "hour": 8,
                "weekday": 2,
                "is_weekend": 0,
                "time_to_station": 155,
                "roll_mean_tts_10m": 160,
                "roll_max_tts_10m": 190,
                "roll_count_10m": 5,
                "baseline_median_tts": 190,
                "deviation_from_baseline": -35,
            },
        },
    ]

    history = [
        {"timestamp": "2026-03-29T14:25:00+00:00", "station": "Oxford Circus Underground Station", "prob": 0.34},
        {"timestamp": "2026-03-29T14:28:00+00:00", "station": "Oxford Circus Underground Station", "prob": 0.49},
        {"timestamp": "2026-03-29T14:31:00+00:00", "station": "Oxford Circus Underground Station", "prob": 0.67},
        {"timestamp": "2026-03-29T14:35:00+00:00", "station": "Oxford Circus Underground Station", "prob": 0.84},
        {"timestamp": "2026-03-29T14:40:00+00:00", "station": "Oxford Circus Underground Station", "prob": 0.91},

        {"timestamp": "2026-03-29T14:25:00+00:00", "station": "Waterloo Underground Station", "prob": 0.28},
        {"timestamp": "2026-03-29T14:28:00+00:00", "station": "Waterloo Underground Station", "prob": 0.39},
        {"timestamp": "2026-03-29T14:31:00+00:00", "station": "Waterloo Underground Station", "prob": 0.55},
        {"timestamp": "2026-03-29T14:35:00+00:00", "station": "Waterloo Underground Station", "prob": 0.68},
        {"timestamp": "2026-03-29T14:40:00+00:00", "station": "Waterloo Underground Station", "prob": 0.84},

        {"timestamp": "2026-03-29T14:25:00+00:00", "station": "Green Park Underground Station", "prob": 0.12},
        {"timestamp": "2026-03-29T14:28:00+00:00", "station": "Green Park Underground Station", "prob": 0.17},
        {"timestamp": "2026-03-29T14:31:00+00:00", "station": "Green Park Underground Station", "prob": 0.26},
        {"timestamp": "2026-03-29T14:35:00+00:00", "station": "Green Park Underground Station", "prob": 0.44},
        {"timestamp": "2026-03-29T14:40:00+00:00", "station": "Green Park Underground Station", "prob": 0.73},
    ]

    return {
        "source": "showcase_demo",
        "count": len(results),
        "results": results,
        "status": None,
        "history": history,
    }


def render_status_card(label, value, sub, tone="blue"):
    st.markdown(
        f"""
        <div class="status-card {tone}">
            <div class="status-label">{label}</div>
            <div class="status-value">{value}</div>
            <div class="status-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_chip(label, value, sub):
    st.markdown(
        f"""
        <div class="summary-chip">
            <div class="summary-chip-label">{label}</div>
            <div class="summary-chip-value">{value}</div>
            <div class="summary-chip-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    if HERO_IMAGE.exists():
        img_bytes = HERO_IMAGE.read_bytes()
        img_base64 = base64.b64encode(img_bytes).decode()
        st.markdown(
            f"""
            <div class="hero-banner"
                 style="background-image: url('data:image/png;base64,{img_base64}');">
                <div class="hero-content">
                    <div class="hero-title-overlay">DelaySense</div>
                    <div class="hero-sub-overlay">
                        Real-time early warning for London Underground arrivals
                    </div>
                    <div class="hero-sub-overlay">
                        Live monitoring, short-horizon delay risk, and context-aware arrival intelligence
                    </div>
                    <div class="hero-tag-row">
                        <span class="hero-tag">Live monitor</span>
                        <span class="hero-tag">Recent context</span>
                        <span class="hero-tag">Forecasting-driven</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="panel">
                <div class="section-title" style="font-size:2rem; margin-bottom:0.2rem;">DelaySense</div>
                <div style="color:#667085; font-size:1rem;">
                    Real-time early warning dashboard for London Underground arrivals
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def format_model_name(model_info):
    if not model_info:
        return "ML Model"
    name = (
        model_info.get("model_name")
        or model_info.get("model_family")
        or ""
    )
    lowered = str(name).lower()
    if "lightgbm" in lowered:
        return "LightGBM"
    if "xgboost" in lowered:
        return "XGBoost"
    if "logistic" in lowered:
        return "Logistic Regression"
    if "randomforest" in lowered or "random_forest" in lowered:
        return "Random Forest"
    return str(name) if name else "ML Model"


def fetch_health():
    response = requests.get(f"{API_URL}/health", timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_live_monitoring():
    response = requests.get(f"{API_URL}/monitor/live", timeout=20)
    response.raise_for_status()
    return response.json()


def manual_refresh_live_monitor():
    response = requests.post(f"{API_URL}/monitor/refresh", timeout=25)
    response.raise_for_status()
    return response.json()


def format_seconds_human(seconds):
    total_seconds = max(0, int(round(float(seconds))))
    if total_seconds < 60:
        return f"{total_seconds}s"
    mins = total_seconds // 60
    secs = total_seconds % 60
    if secs == 0:
        return f"{mins}m"
    return f"{mins}m {secs}s"


def format_delta_human(delta_seconds):
    delta_seconds = float(delta_seconds)
    if abs(delta_seconds) < 1:
        return "On time"
    if delta_seconds > 0:
        return f"{format_seconds_human(delta_seconds)} delay"
    return f"{format_seconds_human(abs(delta_seconds))} faster"


def parse_iso_to_local_string(value):
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        dt_local = dt.astimezone()   # convert to local machine timezone
        return dt_local.strftime("%H:%M:%S")
    except Exception:
        return str(value)


def monitor_readiness_text(status):
    if not status:
        return "—"
    warmup_minutes = float(status.get("warmup_minutes", 0))
    state = str(status.get("warmup_status", "unknown")).lower()
    if state == "warm":
        return f"Ready ({warmup_minutes:.1f} min collected)"
    if state == "warming":
        return f"Collecting recent data ({warmup_minutes:.1f} / 10 min)"
    return "Starting up"


def overall_risk_label(avg_prob):
    if avg_prob >= 0.60:
        return "High"
    if avg_prob >= 0.30:
        return "Medium"
    return "Low"


def apply_plot_style(fig):
    fig.update_layout(
        paper_bgcolor=COLORS["plot_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color=COLORS["text_main"], size=13),
        showlegend=False,
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        title=None,
        tickfont=dict(size=12),
    )
    fig.update_yaxes(
        gridcolor="rgba(20,33,61,0.10)",
        zeroline=False,
        title=None,
        tickfont=dict(size=12),
    )
    return fig


def fig_current_vs_usual(current_sec, usual_sec):
    current_min = round(current_sec / 60, 2)
    usual_min = round(usual_sec / 60, 2)

    df = pd.DataFrame(
        {
            "Metric": ["Current arrival", "Usual arrival"],
            "Minutes": [current_min, usual_min],
        }
    )

    fig = px.bar(
        df,
        x="Metric",
        y="Minutes",
        color="Metric",
        color_discrete_map={
            "Current arrival": COLORS["navy"],
            "Usual arrival": COLORS["navy_light"],
        },
        text="Minutes",
    )
    fig.update_traces(
        texttemplate="%{text:.1f} min",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="%{x}: %{y:.1f} min<extra></extra>",
    )
    return apply_plot_style(fig)


def fig_likelihood_across_arrivals(monitor_results):
    rows = []
    for r in monitor_results:
        rows.append(
            {
                "Station": r["display"]["stop_name"],
                "Likelihood": float(r["prob"]),
                "Risk": str(r["risk"]).upper(),
            }
        )

    df = pd.DataFrame(rows).sort_values("Likelihood", ascending=True)

    fig = px.bar(
        df,
        x="Likelihood",
        y="Station",
        orientation="h",
        color="Risk",
        color_discrete_map={
            "HIGH": COLORS["high"],
            "MEDIUM": COLORS["medium"],
            "LOW": COLORS["low"],
        },
        text="Likelihood",
    )
    fig.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="%{y}: %{x:.1%}<extra></extra>",
    )
    fig.update_xaxes(range=[0, 1], tickformat=".0%")
    return apply_plot_style(fig)


def fig_network_snapshot(monitor_results):
    rows = []
    for r in monitor_results:
        features = r["features"]
        display = r["display"]
        rows.append(
            {
                "Station": display["stop_name"],
                "CurrentArrivalMin": float(features["time_to_station"]) / 60.0,
                "DelayLikelihood": float(r["prob"]),
                "ExtraDelayMin": abs(float(features["deviation_from_baseline"])) / 60.0,
                "Risk": str(r["risk"]).upper(),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return None

    fig = px.scatter(
        df,
        x="CurrentArrivalMin",
        y="DelayLikelihood",
        size="ExtraDelayMin",
        color="Risk",
        hover_name="Station",
        size_max=34,
        color_discrete_map={
            "HIGH": COLORS["high"],
            "MEDIUM": COLORS["medium"],
            "LOW": COLORS["low"],
        },
    )
    fig.update_traces(
        marker=dict(line=dict(width=1, color="rgba(255,255,255,0.85)")),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Current arrival: %{x:.1f} min<br>"
            "Delay likelihood: %{y:.1%}<br>"
            "<extra></extra>"
        ),
    )
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    fig.update_xaxes(title="Current arrival (min)")
    return apply_plot_style(fig)


def fig_selected_station_trend(selected_station, source_label):
    if str(source_label).startswith("tfl_live"):
        history = st.session_state.get("live_history", [])
    else:
        history = st.session_state.get("showcase_history", [])

    if not history:
        return None

    df = pd.DataFrame(history)
    if df.empty:
        return None

    df = df[df["station"] == selected_station].copy()
    if df.empty or len(df) < 2:
        return None

    df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("timestamp_dt")

    fig = px.line(
        df,
        x="timestamp_dt",
        y="prob",
        markers=True,
    )
    fig.update_traces(
        line=dict(width=3, color=COLORS["blue_soft"]),
        hovertemplate="%{x|%H:%M:%S}<br>Delay likelihood: %{y:.1%}<extra></extra>",
    )
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    fig.update_xaxes(title=None)
    return apply_plot_style(fig)

def selected_arrival_micro_hint(features):
    delta = float(features["deviation_from_baseline"])
    if delta > 120:
        return "Currently slower than usual"
    if delta < -120:
        return "Currently faster than usual"
    return "Currently close to usual conditions"


def build_monitoring_table(results):
    rows = []
    for result in results:
        display = result["display"]
        features = result["features"]

        risk = result["risk"].upper()
        if risk == "HIGH":
            icon = "🔴"
        elif risk == "MEDIUM":
            icon = "🟠"
        else:
            icon = "🟢"

        line_name = str(display.get("line_id", "")).title()
        direction = str(display.get("direction") or "—").title()

        rows.append(
            {
                "": icon,
                "Station": display["stop_name"],
                "Line": line_name,
                "Direction": direction,
                "Current arrival": format_seconds_human(features["time_to_station"]),
                "Usual arrival": format_seconds_human(features["baseline_median_tts"]),
                "Difference": format_delta_human(features["deviation_from_baseline"]),
                "Delay likelihood": f"{float(result['prob']):.1%}",
                "Risk": risk,
                "Alert": "YES" if result["alert_flag"] else "NO",
                "_sort_likelihood": float(result["prob"]),
                "_sort_delay": float(features["deviation_from_baseline"]),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(
        by=["_sort_likelihood", "_sort_delay"],
        ascending=[False, False],
    ).drop(columns=["_sort_likelihood", "_sort_delay"]).reset_index(drop=True)

    return df


def load_showcase_monitoring():
    payload = build_showcase_demo_payload()
    st.session_state["showcase_history"] = payload.get("history", [])
    return payload


def append_live_history(monitor_results, monitor_status):
    if "live_history" not in st.session_state:
        st.session_state["live_history"] = []

    ts = monitor_status.get("last_success_at") or monitor_status.get("last_poll_at")
    if not ts:
        return

    existing_keys = {
        (item["timestamp"], item["station"])
        for item in st.session_state["live_history"]
    }

    for r in monitor_results:
        station = r["display"]["stop_name"]
        key = (ts, station)
        if key in existing_keys:
            continue

        features = r["features"]
        st.session_state["live_history"].append(
            {
                "timestamp": ts,
                "station": station,
                "prob": float(r["prob"]),
                "current_arrival_min": float(features["time_to_station"]) / 60.0,
                "usual_arrival_min": float(features["baseline_median_tts"]) / 60.0,
                "extra_delay_min": float(features["deviation_from_baseline"]) / 60.0,
                "risk": str(r["risk"]).upper(),
            }
        )

    st.session_state["live_history"] = st.session_state["live_history"][-500:]


render_hero()

top_left, top_right = st.columns([1.15, 0.85])

with top_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Controls</div>', unsafe_allow_html=True)

    data_source = st.radio(
        "Monitoring source",
        ["Showcase demo", "Live TfL"],
        index=0,
        horizontal=True,
    )

    selected_mode = st.radio(
        "Alert sensitivity",
        ["Conservative", "Balanced", "Sensitive"],
        index=1,
        horizontal=True,
    )

    include_intelligence = st.checkbox(
        "Show advanced details",
        value=False,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        check_api = st.button("Check API", use_container_width=True)
    with c2:
        load_monitoring = st.button("Start Monitoring", use_container_width=True)
    with c3:
        refresh_live = st.button("Refresh Data", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

with top_right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">System Status</div>', unsafe_allow_html=True)

    health_data = None
    health_error = None

    try:
        health_data = fetch_health()
    except Exception as e:
        health_error = str(e)

    model_display = format_model_name(health_data.get("model_info", {})) if health_data else "ML Model"

    mode_tone = "amber"
    if selected_mode == "Conservative":
        mode_tone = "blue"
    elif selected_mode == "Sensitive":
        mode_tone = "red"

    c1, c2 = st.columns(2)
    with c1:
        render_status_card(
            "API",
            "Online" if health_data else "Offline",
            "Backend reachable" if health_data else "Connection issue",
            tone="green" if health_data else "red",
        )
    with c2:
        render_status_card(
            "Mode",
            selected_mode,
            "Alert profile",
            tone=mode_tone,
        )

    c3, c4 = st.columns(2)
    with c3:
        render_status_card(
            "Model",
            model_display,
            "Prediction engine",
            tone="blue",
        )
    with c4:
        render_status_card(
            "Insights",
            "On" if (health_data and health_data.get("intelligence_enabled")) else "Off",
            "Advanced context",
            tone="green" if (health_data and health_data.get("intelligence_enabled")) else "blue",
        )

    if check_api:
        if health_data:
            st.success("API reachable")
        else:
            st.error(f"API not reachable: {health_error}")

    st.markdown('</div>', unsafe_allow_html=True)

monitor_results = None
monitor_df = None
prediction_error = None
monitor_status = None

if load_monitoring or refresh_live:
    try:
        if data_source == "Live TfL":
            if refresh_live:
                monitoring_payload = manual_refresh_live_monitor()
            else:
                monitoring_payload = fetch_live_monitoring()
        else:
            monitoring_payload = load_showcase_monitoring()

        results = monitoring_payload.get("results", [])
        monitor_status = monitoring_payload.get("status")

        if not results:
            raise ValueError("No arrivals were returned for the selected monitoring source.")

        st.session_state["monitor_results"] = results
        st.session_state["monitor_df"] = build_monitoring_table(results)
        st.session_state["selected_station"] = results[0]["display"]["stop_name"]
        st.session_state["monitor_source"] = monitoring_payload.get("source", "unknown")
        st.session_state["monitor_count"] = monitoring_payload.get("count", len(results))
        st.session_state["selected_mode"] = selected_mode
        st.session_state["data_source"] = data_source
        st.session_state["monitor_status"] = monitor_status

        if data_source == "Live TfL" and monitor_status:
            append_live_history(results, monitor_status)

    except Exception as e:
        prediction_error = str(e)

if "monitor_results" in st.session_state:
    monitor_results = st.session_state["monitor_results"]

if "monitor_df" in st.session_state:
    monitor_df = st.session_state["monitor_df"]

if "monitor_status" in st.session_state:
    monitor_status = st.session_state["monitor_status"]

if prediction_error:
    st.error(f"Prediction failed: {prediction_error}")

if monitor_df is not None and monitor_results is not None:
    probs = [float(r["prob"]) for r in monitor_results]
    alerts_active = sum(1 for r in monitor_results if r["alert_flag"])
    avg_likelihood = float(np.mean(probs)) if probs else 0.0
    avg_risk_text = overall_risk_label(avg_likelihood)
    monitored_count = len(monitor_df)

    if str(st.session_state.get("monitor_source", "")).startswith("showcase"):
        model_display = "Showcase demo"
    else:
        model_display = format_model_name(health_data.get("model_info", {})) if health_data else "ML Model"

    source_label = st.session_state.get("monitor_source", "unknown")
    source_sub = "Live monitor feed" if str(source_label).startswith("tfl_live") else "Curated showcase set"

    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_summary_chip("Monitored arrivals", str(monitored_count), source_sub)
    with summary_cols[1]:
        render_summary_chip("Alerts active", str(alerts_active), "Currently flagged")
    with summary_cols[2]:
        render_summary_chip("Average risk", f"{avg_risk_text} ({avg_likelihood:.1%})", "Across monitored arrivals")
    with summary_cols[3]:
        render_summary_chip("Model in use", model_display, "Current display mode")

    if str(source_label).startswith("tfl_live") and monitor_status:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Live monitor status</div>', unsafe_allow_html=True)

        live_cols = st.columns(4)
        with live_cols[0]:
            render_summary_chip(
                "Monitor",
                "Running" if monitor_status.get("is_running") else "Stopped",
                f'Polling every {monitor_status.get("poll_interval_seconds", "—")}s',
            )
        with live_cols[1]:
            render_summary_chip(
                "Recent context",
                monitor_readiness_text(monitor_status),
                "Rolling features use live short-term history",
            )
        with live_cols[2]:
            render_summary_chip(
                "Last update",
                parse_iso_to_local_string(monitor_status.get("last_success_at")),
                "Latest successful live poll",
            )
        with live_cols[3]:
            render_summary_chip(
                "Live arrivals tracked",
                str(monitor_status.get("latest_result_count", 0)),
                "Current rows in latest live state",
            )

        st.markdown('</div>', unsafe_allow_html=True)

    elif str(source_label).startswith("showcase"):
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Showcase mode</div>', unsafe_allow_html=True)

        demo_cols = st.columns(4)
        with demo_cols[0]:
            render_summary_chip("Delay Scenario", "Mixed Risk Conditions", "Curated mix of high / medium / low risk")
        with demo_cols[1]:
            render_summary_chip("High-risk cases", "3", "To demonstrate urgent attention")
        with demo_cols[2]:
            render_summary_chip("Medium-risk cases", "3", "To demonstrate watchlist behavior")
        with demo_cols[3]:
            render_summary_chip("Low-risk cases", "3", "To show normal conditions")

        st.markdown('</div>', unsafe_allow_html=True)

    table_col, side_col = st.columns([1.38, 0.62])

    with table_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Current arrivals overview</div>', unsafe_allow_html=True)
        st.dataframe(monitor_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with side_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Inspect one arrival</div>', unsafe_allow_html=True)

        station_names = [r["display"]["stop_name"] for r in monitor_results]
        default_index = 0
        if (
            "selected_station" in st.session_state
            and st.session_state["selected_station"] in station_names
        ):
            default_index = station_names.index(st.session_state["selected_station"])

        selected_station = st.selectbox(
            "Choose station",
            station_names,
            index=default_index,
        )
        st.session_state["selected_station"] = selected_station

        selected_result = next(
            r for r in monitor_results if r["display"]["stop_name"] == selected_station
        )

        selected_prob = float(selected_result["prob"])
        selected_alert = selected_result["alert_flag"]
        selected_risk = str(selected_result["risk"]).upper()
        selected_features = selected_result["features"]
        source_display = "Live TfL" if str(source_label).startswith("tfl_live") else "Showcase demo"

        st.markdown(
            f"""
            <div class="inspect-card">
                <div style="font-size:1.2rem; font-weight:800; color:#1f2937; margin-bottom:0.35rem;">
                    {selected_station}
                </div>
                <div style="color:#475467; font-size:0.96rem; margin-bottom:0.6rem;">
                    Delay likelihood: <strong>{selected_prob:.1%}</strong><br>
                    Alert status: <strong>{"YES" if selected_alert else "NO"}</strong><br>
                    Risk level: <strong>{selected_risk}</strong><br>
                    Source: <strong>{source_display}</strong>
                </div>
                <div style="font-size:0.88rem; color:#667085;">
                    {selected_arrival_micro_hint(selected_features)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)

    result = next(
        r for r in monitor_results if r["display"]["stop_name"] == st.session_state["selected_station"]
    )

    display = result["display"]
    features = result["features"]
    prob = float(result["prob"])
    risk = str(result["risk"]).lower()
    explanation = result["explanation"]
    alert_flag = result["alert_flag"]
    current_sec = float(features["time_to_station"])
    usual_sec = float(features["baseline_median_tts"])
    delta_sec = float(features["deviation_from_baseline"])
    source_display = "Live TfL" if str(source_label).startswith("tfl_live") else "Showcase demo"

    st.markdown(
        f"""
        <div class="risk-banner {risk}">
            <div style="font-size:0.82rem; text-transform:uppercase; letter-spacing:0.08em; opacity:0.88; font-weight:800;">
                Selected arrival
            </div>
            <div style="font-size:1.55rem; font-weight:900; margin-top:0.2rem;">
                {display.get("stop_name", "Unknown station")} → {display.get("destination_name", "Unknown destination")}
            </div>
            <div style="margin-top:0.55rem; font-size:1rem;">
                Delay likelihood: <strong>{prob:.1%}</strong> &nbsp; | &nbsp;
                Alert: <strong>{"YES" if alert_flag else "NO"}</strong> &nbsp; | &nbsp;
                Mode: <strong>{selected_mode}</strong> &nbsp; | &nbsp;
                Model: <strong>{model_display}</strong> &nbsp; | &nbsp;
                Source: <strong>{source_display}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What this means</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="explanation-box">{explanation}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Arrival summary</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="kpi-row">
            <div class="kpi-pill">
                <div class="kpi-pill-label">Current arrival</div>
                <div class="kpi-pill-value">{format_seconds_human(current_sec)}</div>
            </div>
            <div class="kpi-pill">
                <div class="kpi-pill-label">Usual arrival</div>
                <div class="kpi-pill-value">{format_seconds_human(usual_sec)}</div>
            </div>
            <div class="kpi-pill">
                <div class="kpi-pill-label">Difference</div>
                <div class="kpi-pill-value">{format_delta_human(delta_sec)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="muted" style="font-size:0.95rem; margin-top:0.95rem;">
            Station: <strong>{display.get("stop_name", "Unknown")}</strong> &nbsp; | &nbsp;
            Line: <strong>{str(display.get("line_id", "")).title()}</strong> &nbsp; | &nbsp;
            Direction: <strong>{str(display.get("direction") or "—").title()}</strong> &nbsp; | &nbsp;
            Platform: <strong>{display.get("platform_name", "Unknown")}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Current vs usual</div>', unsafe_allow_html=True)
        st.plotly_chart(
            fig_current_vs_usual(current_sec, usual_sec),
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with chart_col2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Selected arrival trend</div>', unsafe_allow_html=True)
        trend_fig = fig_selected_station_trend(
            st.session_state["selected_station"],
            source_label,
        )
        if trend_fig is not None:
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("Trend becomes visible after a few refreshes for the selected station.")
        st.markdown('</div>', unsafe_allow_html=True)

    lower_col1, lower_col2 = st.columns(2)

    with lower_col1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Likelihood across monitored arrivals</div>', unsafe_allow_html=True)
        st.plotly_chart(
            fig_likelihood_across_arrivals(monitor_results),
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with lower_col2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Live network snapshot</div>', unsafe_allow_html=True)
        snapshot_fig = fig_network_snapshot(monitor_results)
        if snapshot_fig is not None:
            st.plotly_chart(snapshot_fig, use_container_width=True)
        else:
            st.info("No snapshot data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    if result.get("intelligence") and include_intelligence and str(source_label).startswith("tfl_live"):
        intelligence = result["intelligence"]

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Additional context</div>', unsafe_allow_html=True)

        summary_text = intelligence.get("summary") or intelligence.get("narrative") or "Additional context available."
        st.markdown(
            f'<div class="explanation-box">{summary_text}</div>',
            unsafe_allow_html=True,
        )

        similar_cases = intelligence.get("similar_cases")
        if similar_cases:
            st.markdown('<div style="height:0.7rem;"></div>', unsafe_allow_html=True)
            st.write("Similar historical cases")
            st.dataframe(pd.DataFrame(similar_cases), use_container_width=True, hide_index=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Advanced technical details", expanded=False):
        st.code(json.dumps(result, indent=2), language="json")

else:
    st.markdown(
        """
        <div class="panel">
            <div class="empty-state">
                Click <strong>Start Monitoring</strong> to load either the curated showcase demo
                or the current live TfL monitor state, compare delay likelihoods across arrivals,
                and inspect one case in detail.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )