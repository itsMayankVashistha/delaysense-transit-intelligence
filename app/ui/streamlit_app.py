from pathlib import Path
from datetime import datetime
import base64
import json

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = "http://localhost:8000"
HERO_IMAGE = Path("app/ui/assets/banner1.png")

SAMPLE_CASES = [
    {
        "stop_id": "940GZZLUOXC",
        "stop_name": "Oxford Circus",
        "line_id": "victoria",
        "direction": "northbound",
        "platform_name": "Northbound Platform",
        "destination_name": "Walthamstow Central",
        "time_to_station": 660,
    },
    {
        "stop_id": "940GZZLUGPK",
        "stop_name": "Green Park",
        "line_id": "victoria",
        "direction": "southbound",
        "platform_name": "Southbound Platform",
        "destination_name": "Brixton",
        "time_to_station": 420,
    },
    {
        "stop_id": "940GZZLUBXN",
        "stop_name": "Brixton",
        "line_id": "victoria",
        "direction": "northbound",
        "platform_name": "Northbound Platform",
        "destination_name": "Walthamstow Central",
        "time_to_station": 900,
    },
    {
        "stop_id": "940GZZLUWLO",
        "stop_name": "Waterloo",
        "line_id": "jubilee",
        "direction": "eastbound",
        "platform_name": "Eastbound Platform",
        "destination_name": "Stratford",
        "time_to_station": 300,
    },
    {
        "stop_id": "940GZZLUSTD",
        "stop_name": "Stratford",
        "line_id": "jubilee",
        "direction": "westbound",
        "platform_name": "Westbound Platform",
        "destination_name": "Stanmore",
        "time_to_station": 720,
    },
]

COLORS = {
    "bg_top_left": "rgba(124,147,195,0.10)",
    "bg_top_right": "rgba(232,93,117,0.08)",
    "bg_start": "#f7f9fc",
    "bg_end": "#eef3f9",
    "text_main": "#14213D",
    "text_soft": "#667085",
    "panel_border": "rgba(214,223,235,0.7)",
    "high": "#E85D75",
    "high_dark": "#D94B64",
    "medium": "#F6AE2D",
    "medium_dark": "#E39115",
    "low": "#4CAF7D",
    "low_dark": "#2F8F68",
    "navy": "#23395B",
    "navy_light": "#7C93C3",
    "plot_bg": "rgba(255,255,255,0)",
}

st.set_page_config(
    page_title="TfL Delay Intelligence",
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
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }}

    .panel {{
        background: rgba(255,255,255,0.92);
        backdrop-filter: blur(10px);
        border-radius: 22px;
        padding: 1rem 1rem 0.95rem 1rem;
        box-shadow: 0 10px 28px rgba(20,33,61,0.08);
        border: 1px solid {COLORS["panel_border"]};
        margin-bottom: 1rem;
    }}

    .section-title {{
        font-size: 1.08rem;
        font-weight: 700;
        color: {COLORS["text_main"]};
        margin-bottom: 0.7rem;
    }}

    .mini-card {{
        background: rgba(255,255,255,0.95);
        border-radius: 20px;
        padding: 1rem;
        box-shadow: 0 10px 24px rgba(20,33,61,0.07);
        border: 1px solid {COLORS["panel_border"]};
        min-height: 130px;
    }}

    .mini-label {{
        font-size: 0.9rem;
        color: {COLORS["text_soft"]};
        margin-bottom: 0.25rem;
    }}

    .mini-value {{
        font-size: 1.95rem;
        font-weight: 800;
        color: {COLORS["text_main"]};
        line-height: 1.1;
    }}

    .mini-sub {{
        margin-top: 0.35rem;
        font-size: 0.85rem;
        color: {COLORS["text_soft"]};
    }}

    .hero-banner {{
        position: relative;
        min-height: 265px;
        border-radius: 28px;
        overflow: hidden;
        margin-bottom: 1.1rem;
        background-size: cover;
        background-position: center center;
        box-shadow: 0 18px 40px rgba(20,33,61,0.15);
        border: 1px solid rgba(255,255,255,0.35);
    }}

    .hero-banner::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(
            90deg,
            rgba(20,33,61,0.86) 0%,
            rgba(20,33,61,0.62) 38%,
            rgba(20,33,61,0.22) 68%,
            rgba(20,33,61,0.08) 100%
        );
    }}

    .hero-content {{
        position: relative;
        z-index: 2;
        padding: 1.8rem 2rem;
        max-width: 760px;
    }}

    .hero-title-overlay {{
        font-size: 2.35rem;
        font-weight: 900;
        color: white;
        line-height: 1.05;
        margin-bottom: 0.55rem;
    }}

    .hero-sub-overlay {{
        color: rgba(255,255,255,0.88);
        font-size: 1rem;
        line-height: 1.5;
        margin-bottom: 0.2rem;
    }}

    .hero-tag-row {{
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }}

    .hero-tag {{
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.20);
        color: white;
        padding: 0.42rem 0.75rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
    }}

    .summary-chip {{
        background: white;
        border-radius: 18px;
        padding: 0.95rem 1rem;
        border: 1px solid {COLORS["panel_border"]};
        box-shadow: 0 8px 20px rgba(20,33,61,0.05);
        min-height: 105px;
    }}

    .summary-chip-label {{
        font-size: 0.85rem;
        color: {COLORS["text_soft"]};
        margin-bottom: 0.2rem;
    }}

    .summary-chip-value {{
        font-size: 1.45rem;
        font-weight: 800;
        color: {COLORS["text_main"]};
        line-height: 1.1;
    }}

    .summary-chip-sub {{
        margin-top: 0.35rem;
        font-size: 0.82rem;
        color: {COLORS["text_soft"]};
    }}

    .risk-banner {{
        border-radius: 22px;
        padding: 1.1rem 1.25rem;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 12px 28px rgba(20,33,61,0.12);
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

    .kpi-row {{
        display: flex;
        gap: 0.8rem;
        flex-wrap: wrap;
        margin-top: 0.2rem;
    }}

    .kpi-pill {{
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(220,227,238,0.95);
        border-radius: 18px;
        padding: 0.85rem 1rem;
        min-width: 165px;
        box-shadow: 0 8px 18px rgba(20,33,61,0.04);
    }}

    .kpi-pill-label {{
        font-size: 0.78rem;
        color: {COLORS["text_soft"]};
        margin-bottom: 0.2rem;
    }}

    .kpi-pill-value {{
        font-size: 1.12rem;
        font-weight: 800;
        color: {COLORS["text_main"]};
    }}

    .explanation-box {{
        background: rgba(255,255,255,0.92);
        border: 1px solid {COLORS["panel_border"]};
        border-radius: 18px;
        padding: 1rem 1.05rem;
        color: {COLORS["text_main"]};
        line-height: 1.65;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
    }}

    .inspect-card {{
        background: white;
        border: 1px solid {COLORS["panel_border"]};
        border-radius: 20px;
        padding: 1rem;
        box-shadow: 0 10px 22px rgba(20,33,61,0.05);
    }}

    .muted {{
        color: {COLORS["text_soft"]};
    }}

    div[data-testid="stDataFrame"] {{
        border-radius: 18px;
        overflow: hidden;
    }}

    .empty-state {{
        padding: 2.7rem 1rem;
        text-align: center;
        color: {COLORS["text_soft"]};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_small_card(label, value, sub):
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">{label}</div>
            <div class="mini-value">{value}</div>
            <div class="mini-sub">{sub}</div>
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
                    <div class="hero-title-overlay">TfL Delay Intelligence</div>
                    <div class="hero-sub-overlay">
                        Real-time early warning for London Underground arrivals
                    </div>
                    <div class="hero-sub-overlay">
                        Live monitoring, short-horizon delay risk, and context-aware arrival intelligence
                    </div>
                    <div class="hero-tag-row">
                        <span class="hero-tag">Live monitor</span>
                        <span class="hero-tag">Risk analysis</span>
                        <span class="hero-tag">Early warning intelligence</span>
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
                <div class="section-title" style="font-size:2rem; margin-bottom:0.2rem;">TfL Delay Intelligence</div>
                <div style="color:#667085; font-size:1rem;">
                    Real-time early warning dashboard for London Underground arrivals
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def fetch_health():
    response = requests.get(f"{API_URL}/health", timeout=10)
    response.raise_for_status()
    return response.json()


def predict_case(case, mode, include_intelligence):
    payload = {
        "observed_at": case.get("observed_at", 1772357400000),
        "stop_id": case["stop_id"],
        "stop_name": case["stop_name"],
        "line_id": case["line_id"],
        "vehicle_id": case.get("vehicle_id", f"demo_{case['stop_id']}"),
        "direction": case["direction"],
        "platform_name": case["platform_name"],
        "destination_name": case["destination_name"],
        "time_to_station": case["time_to_station"],
        "alert_mode": mode,
        "include_intelligence": include_intelligence,
    }
    response = requests.post(f"{API_URL}/predict", json=payload, timeout=20)
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


def load_sample_monitoring(mode, include_intelligence):
    results = []
    for case in SAMPLE_CASES:
        results.append(predict_case(case, mode, include_intelligence))
    return {
        "source": "sample",
        "count": len(results),
        "results": results,
        "status": None,
    }


def format_seconds_human(seconds):
    total_seconds = max(0, int(round(float(seconds))))

    if total_seconds < 60:
        return f"{total_seconds}s"

    mins = total_seconds // 60
    secs = total_seconds % 60

    if secs == 0:
        return f"{mins}m"

    return f"{mins}m {secs}s"


def parse_iso_to_local_string(value):
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return str(value)


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


def fig_delay_signal(threshold_value, prob):
    df = pd.DataFrame(
        {
            "Type": ["Alert threshold", "Delay likelihood"],
            "Value": [threshold_value, prob],
            "Color": [
                COLORS["navy_light"],
                COLORS["high"] if prob >= threshold_value else COLORS["medium"],
            ],
        }
    )

    fig = px.bar(
        df,
        x="Type",
        y="Value",
        color="Type",
        color_discrete_sequence=df["Color"].tolist(),
        text="Value",
    )
    fig.update_traces(
        texttemplate="%{text:.0%}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="%{x}: %{y:.0%}<extra></extra>",
    )
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    return apply_plot_style(fig)


def fig_likelihood_across_arrivals(monitor_results):
    rows = []
    for r in monitor_results:
        rows.append(
            {
                "Station": r["display"]["stop_name"],
                "Likelihood": float(r["prob"]),
            }
        )

    df = pd.DataFrame(rows).sort_values("Likelihood", ascending=True)

    colors = []
    for v in df["Likelihood"]:
        if v >= 0.70:
            colors.append(COLORS["high"])
        elif v >= 0.40:
            colors.append(COLORS["medium"])
        else:
            colors.append(COLORS["low"])

    fig = px.bar(
        df,
        x="Likelihood",
        y="Station",
        orientation="h",
        color="Station",
        color_discrete_sequence=colors,
        text="Likelihood",
    )
    fig.update_traces(
        texttemplate="%{text:.0%}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="%{y}: %{x:.0%}<extra></extra>",
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
                "ExtraDelayMin": max(0.0, float(features["deviation_from_baseline"]) / 60.0),
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
        marker=dict(line=dict(width=1, color="rgba(255,255,255,0.8)")),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Current arrival: %{x:.1f} min<br>"
            "Delay likelihood: %{y:.0%}<br>"
            "<extra></extra>"
        ),
    )
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    fig.update_xaxes(title="Current arrival (min)")
    return apply_plot_style(fig)


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


def fig_selected_station_trend(selected_station):
    history = st.session_state.get("live_history", [])
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
        line=dict(width=3),
        hovertemplate="%{x|%H:%M:%S}<br>Delay likelihood: %{y:.0%}<extra></extra>",
    )
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    fig.update_xaxes(title=None)
    return apply_plot_style(fig)


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

        deviation = float(features["deviation_from_baseline"])
        if deviation > 0:
            extra_delay = f"+{format_seconds_human(deviation)}"
        elif deviation < 0:
            extra_delay = f"-{format_seconds_human(abs(deviation))}"
        else:
            extra_delay = "0s"

        rows.append(
            {
                "": icon,
                "Station": display["stop_name"],
                "Line": str(display["line_id"]).title(),
                "Direction": str(display["direction"]).title(),
                "Destination": display.get("destination_name", "Unknown"),
                "Current arrival": format_seconds_human(features["time_to_station"]),
                "Usual arrival": format_seconds_human(features["baseline_median_tts"]),
                "Extra delay": extra_delay,
                "Delay likelihood": f"{round(float(result['prob']) * 100)}%",
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


render_hero()

top_left, top_right = st.columns([1.15, 0.85])

with top_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Controls</div>', unsafe_allow_html=True)

    data_source = st.radio(
        "Monitoring source",
        ["Sample demo", "Live TfL"],
        index=1,
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

    c1, c2 = st.columns(2)
    with c1:
        render_small_card(
            "API",
            "Online" if health_data else "Offline",
            "Backend reachable" if health_data else "Connection issue",
        )
    with c2:
        render_small_card(
            "Mode",
            selected_mode,
            "Alert profile",
        )

    c3, c4 = st.columns(2)
    with c3:
        render_small_card(
            "Model",
            health_data.get("model_source", "unknown") if health_data else "unknown",
            "Inference backend",
        )
    with c4:
        render_small_card(
            "Advanced insights",
            "On" if (health_data and health_data.get("intelligence_enabled")) else "Off",
            "Optional enrichment",
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
            monitoring_payload = load_sample_monitoring(
                selected_mode,
                include_intelligence,
            )

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
    alerts_active = sum(1 for r in monitor_results if r["alert_flag"])
    avg_likelihood = sum(float(r["prob"]) for r in monitor_results) / len(monitor_results)
    monitored_count = len(monitor_df)
    model_source = health_data.get("model_source", "unknown") if health_data else "unknown"
    source_label = st.session_state.get("monitor_source", "unknown")
    source_sub = "Live TfL feed" if source_label == "tfl_live" else "Demo watchlist"

    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_summary_chip("Monitored arrivals", str(monitored_count), source_sub)
    with summary_cols[1]:
        render_summary_chip("Alerts active", str(alerts_active), "Currently flagged")
    with summary_cols[2]:
        render_summary_chip("Average likelihood", f"{avg_likelihood:.0%}", "Across monitored arrivals")
    with summary_cols[3]:
        render_summary_chip("Model source", str(model_source), "Current backend")

    if source_label.startswith("tfl_live") and monitor_status:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Live monitor status</div>', unsafe_allow_html=True)

        live_cols = st.columns(4)
        with live_cols[0]:
            render_summary_chip(
                "Monitor",
                "Running" if monitor_status.get("is_running") else "Stopped",
                f'Poll every {monitor_status.get("poll_interval_seconds", "—")}s',
            )
        with live_cols[1]:
            render_summary_chip(
                "Rolling context",
                str(monitor_status.get("warmup_status", "unknown")).title(),
                f'{monitor_status.get("warmup_minutes", 0)} min warm-up',
            )
        with live_cols[2]:
            render_summary_chip(
                "Last update",
                parse_iso_to_local_string(monitor_status.get("last_success_at")),
                "Latest successful poll",
            )
        with live_cols[3]:
            render_summary_chip(
                "Poll count",
                str(monitor_status.get("poll_count", 0)),
                "Background cycles completed",
            )

        st.markdown('</div>', unsafe_allow_html=True)

    table_col, side_col = st.columns([1.35, 0.65])

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
        source_display = "Live TfL" if source_label.startswith("tfl_live") else "Sample demo"

        st.markdown(
            f"""
            <div class="inspect-card">
                <div style="font-size:1.2rem; font-weight:700; color:#1f2937; margin-bottom:0.35rem;">
                    {selected_station}
                </div>
                <div style="color:#475467; font-size:0.96rem; margin-bottom:0.75rem;">
                    Delay likelihood: <strong>{selected_prob:.0%}</strong><br>
                    Alert status: <strong>{"YES" if selected_alert else "NO"}</strong><br>
                    Risk level: <strong>{selected_risk}</strong><br>
                    Source: <strong>{source_display}</strong>
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
    alert_threshold = float(result.get("alert_threshold", 0.60))
    current_sec = float(features["time_to_station"])
    usual_sec = float(features["baseline_median_tts"])
    extra_delay_sec = current_sec - usual_sec
    source_display = "Live TfL" if source_label.startswith("tfl_live") else "Sample demo"

    st.markdown(
        f"""
        <div class="risk-banner {risk}">
            <div style="font-size:0.82rem; text-transform:uppercase; letter-spacing:0.08em; opacity:0.88; font-weight:700;">
                Selected arrival
            </div>
            <div style="font-size:1.55rem; font-weight:800; margin-top:0.2rem;">
                {display.get("stop_name", "Unknown station")} → {display.get("destination_name", "Unknown destination")}
            </div>
            <div style="margin-top:0.55rem; font-size:1rem;">
                Delay likelihood: <strong>{prob:.0%}</strong> &nbsp; | &nbsp;
                Alert: <strong>{"YES" if alert_flag else "NO"}</strong> &nbsp; | &nbsp;
                Mode: <strong>{selected_mode}</strong> &nbsp; | &nbsp;
                Model: <strong>{result.get("model_source", "unknown")}</strong> &nbsp; | &nbsp;
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
                <div class="kpi-pill-label">Extra delay</div>
                <div class="kpi-pill-value">
                    {f"+{format_seconds_human(extra_delay_sec)}" if extra_delay_sec > 0 else f"-{format_seconds_human(abs(extra_delay_sec))}" if extra_delay_sec < 0 else "0s"}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="muted" style="font-size:0.95rem; margin-top:0.9rem;">
            Station: <strong>{display.get("stop_name", "Unknown")}</strong> &nbsp; | &nbsp;
            Line: <strong>{str(display.get("line_id", "")).title()}</strong> &nbsp; | &nbsp;
            Direction: <strong>{str(display.get("direction", "")).title()}</strong> &nbsp; | &nbsp;
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
        st.markdown('<div class="section-title">Delay likelihood</div>', unsafe_allow_html=True)
        st.plotly_chart(
            fig_delay_signal(alert_threshold, prob),
            use_container_width=True,
        )
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

    if source_label.startswith("tfl_live"):
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Selected arrival trend</div>', unsafe_allow_html=True)

        trend_fig = fig_selected_station_trend(st.session_state["selected_station"])
        if trend_fig is not None:
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("Trend becomes visible after a few live refreshes for the selected station.")

        st.markdown('</div>', unsafe_allow_html=True)

    if result.get("intelligence"):
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
                Click <strong>Load Monitoring View</strong> to load either the sample demo set
                or the current live TfL monitor state, compare delay likelihoods across stations,
                and inspect one arrival in detail.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )