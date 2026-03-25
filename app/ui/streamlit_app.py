from pathlib import Path
import base64

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
        line-height: 1.15;
    }}

    .mini-sub {{
        font-size: 0.88rem;
        color: {COLORS["text_soft"]};
        margin-top: 0.28rem;
    }}

    .risk-banner {{
        border-radius: 24px;
        padding: 1.25rem 1.2rem 1rem 1.2rem;
        color: white;
        box-shadow: 0 14px 32px rgba(0,0,0,0.10);
        margin-bottom: 1rem;
    }}

    .risk-low {{
        background: linear-gradient(135deg, {COLORS["low"]} 0%, {COLORS["low_dark"]} 100%);
    }}

    .risk-medium {{
        background: linear-gradient(135deg, {COLORS["medium"]} 0%, {COLORS["medium_dark"]} 100%);
    }}

    .risk-high {{
        background: linear-gradient(135deg, {COLORS["high"]} 0%, {COLORS["high_dark"]} 100%);
    }}

    .pill {{
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-top: 0.35rem;
        color: white;
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.14);
        backdrop-filter: blur(4px);
    }}

    .explanation-box {{
        background: #F1F6FF;
        color: #17365F;
        border: 1px solid #D7E6FB;
        border-radius: 18px;
        padding: 1rem;
        font-size: 1.03rem;
        line-height: 1.6;
    }}

    .select-card {{
        background:#F9FBFD;
        border:1px solid #E3EAF4;
        border-radius:18px;
        padding:1rem;
        margin-top:0.8rem;
    }}

    .empty-box {{
        background: linear-gradient(135deg, #F8FBFF 0%, #EEF5FF 100%);
        border: 1px dashed #C6D8F0;
        border-radius: 22px;
        padding: 2rem 1.2rem;
        text-align: center;
        color: #38537A;
    }}

    .hero-banner {{
        position: relative;
        width: 100%;
        height: 250px;
        border-radius: 26px;
        overflow: hidden;
        margin-bottom: 1rem;
        box-shadow: 0 14px 34px rgba(0,0,0,0.12);
        background-size: cover;
        background-repeat: no-repeat;
        background-position: 72% 42%;
    }}

    .hero-banner::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(
            90deg,
            rgba(15, 23, 42, 0.82) 0%,
            rgba(15, 23, 42, 0.72) 28%,
            rgba(15, 23, 42, 0.38) 52%,
            rgba(15, 23, 42, 0.08) 100%
        );
    }}

    .hero-content {{
        position: relative;
        z-index: 2;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 28px 30px;
        max-width: 46%;
        color: white;
    }}

    .hero-title-overlay {{
        font-size: 2.15rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.45rem;
        letter-spacing: -0.02em;
    }}

    .hero-sub-overlay {{
        font-size: 1.02rem;
        opacity: 0.96;
        margin-bottom: 0.25rem;
        line-height: 1.45;
    }}

    .hero-tag-row {{
        margin-top: 0.7rem;
    }}

    .hero-tag {{
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.45rem;
        margin-top: 0.3rem;
        color: white;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.14);
        backdrop-filter: blur(4px);
    }}

    div[data-testid="stMetric"] {{
        background: white;
        border: 1px solid {COLORS["panel_border"]};
        padding: 0.9rem 1rem;
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(15,23,42,0.06);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def format_seconds_human(seconds: float) -> str:
    seconds = int(round(float(seconds)))
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{sign}{minutes}m {secs:02d}s"


def fetch_health():
    response = requests.get(f"{API_URL}/health", timeout=5)
    response.raise_for_status()
    return response.json()


def get_threshold(selected_mode: str) -> float:
    if selected_mode == "Conservative":
        return 0.80
    if selected_mode == "Sensitive":
        return 0.40
    return 0.60


def render_small_card(label, value, sub=""):
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


def predict_case(case, mode, include_intelligence):
    payload = {
        "observed_at": 1772357400000,
        "stop_id": case["stop_id"],
        "stop_name": case["stop_name"],
        "line_id": case["line_id"],
        "vehicle_id": f"demo_{case['stop_id']}",
        "direction": case["direction"],
        "platform_name": case["platform_name"],
        "destination_name": case["destination_name"],
        "time_to_station": case["time_to_station"],
        "alert_mode": mode,
        "include_intelligence": include_intelligence,
    }

    response = requests.post(
        f"{API_URL}/predict",
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


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

        rows.append(
            {
                "": icon,
                "Station": display["stop_name"],
                "Line": display["line_id"].title(),
                "Direction": display["direction"].title(),
                "Current arrival": format_seconds_human(features["time_to_station"]),
                "Usual arrival": format_seconds_human(features["baseline_median_tts"]),
                "Extra delay": format_seconds_human(features["deviation_from_baseline"]),
                "Delay likelihood": f"{round(result['prob'] * 100)}%",
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
                        Early warning dashboard for London Underground arrival delays
                    </div>
                    <div class="hero-sub-overlay">
                        Forecasting-driven monitoring for current arrival risk
                    </div>
                    <div class="hero-tag-row">
                        <span class="hero-tag">Real-time monitoring</span>
                        <span class="hero-tag">Risk alerts</span>
                        <span class="hero-tag">ML-powered</span>
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
                    Early warning dashboard for London Underground arrival delays
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


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
            "Measure": ["Usual arrival", "Current arrival"],
            "Minutes": [usual_min, current_min],
            "Color": [COLORS["navy_light"], COLORS["high"] if current_min > usual_min else COLORS["low"]],
        }
    )

    fig = px.bar(
        df,
        x="Measure",
        y="Minutes",
        color="Measure",
        color_discrete_sequence=df["Color"].tolist(),
        text="Minutes",
    )
    fig.update_traces(
        texttemplate="%{text:.1f} min",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="%{x}: %{y:.1f} min<extra></extra>",
    )
    fig = apply_plot_style(fig)
    return fig


def fig_recent_pattern(current_sec, recent_avg_sec, recent_worst_sec):
    df = pd.DataFrame(
        {
            "Measure": ["Current", "Recent average", "Recent worst case"],
            "Minutes": [
                round(current_sec / 60, 2),
                round(recent_avg_sec / 60, 2),
                round(recent_worst_sec / 60, 2),
            ],
            "Color": [COLORS["high"], COLORS["navy_light"], COLORS["navy"]],
        }
    )

    fig = px.bar(
        df,
        x="Measure",
        y="Minutes",
        color="Measure",
        color_discrete_sequence=df["Color"].tolist(),
        text="Minutes",
    )
    fig.update_traces(
        texttemplate="%{text:.1f} min",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="%{x}: %{y:.1f} min<extra></extra>",
    )
    fig = apply_plot_style(fig)
    return fig


def fig_delay_signal(threshold_value, prob):
    df = pd.DataFrame(
        {
            "Type": ["Alert threshold", "Delay likelihood"],
            "Value": [threshold_value, prob],
            "Color": [COLORS["navy_light"], COLORS["high"] if prob >= threshold_value else COLORS["medium"]],
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
    fig.update_yaxes(range=[0, 1])
    fig = apply_plot_style(fig)
    return fig


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
    fig = apply_plot_style(fig)
    return fig


render_hero()

top_left, top_right = st.columns([1.15, 0.85])

with top_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Controls</div>', unsafe_allow_html=True)

    selected_mode = st.radio(
        "Alert sensitivity",
        ["Conservative", "Balanced", "Sensitive"],
        index=1,
        horizontal=True,
    )

    include_intelligence = st.checkbox(
        "Show additional context",
        value=False,
    )

    b1, b2 = st.columns(2)
    with b1:
        check_api = st.button("Check API", use_container_width=True)
    with b2:
        load_monitoring = st.button("Load Monitoring View", use_container_width=True)

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
            "Context",
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

if load_monitoring:
    try:
        results = []
        for case in SAMPLE_CASES:
            results.append(predict_case(case, selected_mode, include_intelligence))

        st.session_state["monitor_results"] = results
        st.session_state["monitor_df"] = build_monitoring_table(results)
        st.session_state["selected_station"] = results[0]["display"]["stop_name"]
    except Exception as e:
        prediction_error = str(e)

if "monitor_results" in st.session_state:
    monitor_results = st.session_state["monitor_results"]

if "monitor_df" in st.session_state:
    monitor_df = st.session_state["monitor_df"]

if prediction_error:
    st.error(f"Prediction failed: {prediction_error}")

if monitor_df is not None and monitor_results is not None:
    alerts_active = sum(1 for r in monitor_results if r["alert_flag"])
    avg_likelihood = round(sum(r["prob"] for r in monitor_results) / len(monitor_results))
    monitored_count = len(monitor_df)
    model_source = health_data.get("model_source", "unknown") if health_data else "unknown"

    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_small_card("Monitored arrivals", str(monitored_count), "Demo watchlist")
    with summary_cols[1]:
        render_small_card("Alerts active", str(alerts_active), "Currently flagged")
    with summary_cols[2]:
        render_small_card("Average likelihood", f"{avg_likelihood:.0%}", "Across monitored arrivals")
    with summary_cols[3]:
        render_small_card("Model source", str(model_source), "Current backend")

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
        if "selected_station" in st.session_state and st.session_state["selected_station"] in station_names:
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

        selected_prob = selected_result["prob"]
        selected_alert = selected_result["alert_flag"]
        selected_risk = selected_result["risk"].upper()

        st.markdown(
            f"""
            <div class="select-card">
                <div style="font-size:1.2rem; font-weight:700; color:#1f2937; margin-bottom:0.35rem;">
                    {selected_station}
                </div>
                <div style="color:#475467; font-size:0.96rem; margin-bottom:0.75rem;">
                    Delay likelihood: <strong>{selected_prob:.0%}</strong><br>
                    Alert status: <strong>{"YES" if selected_alert else "NO"}</strong><br>
                    Risk level: <strong>{selected_risk}</strong>
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
    prob = result["prob"]
    risk = result["risk"]
    explanation = result["explanation"]
    alert_flag = result["alert_flag"]

    current_sec = float(features["time_to_station"])
    usual_sec = float(features["baseline_median_tts"])
    extra_delay_sec = float(features["deviation_from_baseline"])
    recent_avg_sec = float(features["roll_mean_tts_10m"])
    recent_worst_sec = float(features["roll_max_tts_10m"])
    threshold_value = get_threshold(selected_mode)

    current_display = format_seconds_human(current_sec)
    usual_display = format_seconds_human(usual_sec)
    extra_delay_display = format_seconds_human(extra_delay_sec)

    risk_class = f"risk-{risk}"

    st.markdown(
        f"""
        <div class="risk-banner {risk_class}">
            <div style="font-size:1.55rem;font-weight:800;margin-bottom:0.25rem;">
                {display['stop_name']} • {display['line_id'].title()}
            </div>
            <div style="font-size:1rem;opacity:0.96;margin-bottom:0.65rem;">
                {display['direction'].title()} • {display['platform_name']} • Destination: {display['destination_name']}
            </div>
            <div style="font-size:2rem;font-weight:800;line-height:1.1;">
                {risk.upper()} RISK
            </div>
            <div style="margin-top:0.5rem;font-size:1rem;">
                Delay likelihood: <strong>{prob:.0%}</strong> &nbsp; | &nbsp;
                Alert: <strong>{"YES" if alert_flag else "NO"}</strong> &nbsp; | &nbsp;
                Mode: <strong>{selected_mode}</strong> &nbsp; | &nbsp;
                Model: <strong>{model_source}</strong>
            </div>
            <div>
                <span class="pill">Vehicle: {display.get('vehicle_id', 'N/A')}</span>
                <span class="pill">Forecast target: future delay</span>
                <span class="pill">Baseline-aware</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = st.columns(4)
    with cards[0]:
        render_small_card("Current arrival", current_display, "Live predicted arrival time")
    with cards[1]:
        render_small_card("Usual arrival", usual_display, "Typical value for this context")
    with cards[2]:
        render_small_card("Extra delay", extra_delay_display, "Difference from usual pattern")
    with cards[3]:
        render_small_card("System confidence", f"{prob:.0%}", "Estimated delay likelihood")

    left_col, right_col = st.columns([1.15, 0.85])

    with left_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">What this means</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="explanation-box">{explanation}</div>',
            unsafe_allow_html=True,
        )

        snapshot_df = pd.DataFrame(
            [
                {
                    "Station": display["stop_name"],
                    "Line": display["line_id"].title(),
                    "Direction": display["direction"].title(),
                    "Platform": display["platform_name"],
                    "Destination": display["destination_name"],
                    "Current arrival": current_display,
                    "Usual arrival": usual_display,
                    "Extra delay": extra_delay_display,
                    "Alert": "YES" if alert_flag else "NO",
                }
            ]
        )

        st.markdown('<div class="section-title">Selected arrival summary</div>', unsafe_allow_html=True)
        st.dataframe(snapshot_df, use_container_width=True, hide_index=True)

        st.markdown('<div class="section-title">Current vs usual</div>', unsafe_allow_html=True)
        st.plotly_chart(
            fig_current_vs_usual(current_sec, usual_sec),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown('<div class="section-title">Recent pattern</div>', unsafe_allow_html=True)
        st.plotly_chart(
            fig_recent_pattern(current_sec, recent_avg_sec, recent_worst_sec),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Delay likelihood</div>', unsafe_allow_html=True)
        st.plotly_chart(
            fig_delay_signal(threshold_value, prob),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown('<div class="section-title">Likelihood across monitored arrivals</div>', unsafe_allow_html=True)
        st.plotly_chart(
            fig_likelihood_across_arrivals(monitor_results),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown(
            """
            <div class="explanation-box" style="margin-top:0.8rem;">
                <strong>Simple interpretation:</strong><br>
                The system checks whether the current arrival estimate is higher than what is usually expected
                for the same station context, and whether recent conditions are staying elevated.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)

        if include_intelligence and "intelligence" in result:
            intel = result["intelligence"]

            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Additional context</div>', unsafe_allow_html=True)

            summary = intel.get("summary")
            if summary:
                st.write(summary)

            baseline_block = intel.get("baseline")
            if baseline_block:
                st.markdown("**Baseline comparison**")
                st.json(baseline_block)

            rolling_block = intel.get("rolling")
            if rolling_block:
                st.markdown("**Recent behaviour**")
                st.json(rolling_block)

            similar_cases = intel.get("similar_cases")
            if similar_cases:
                st.markdown("**Similar past examples**")
                st.json(similar_cases)

            if "intelligence_error" in result:
                st.warning(f"Additional context error: {result['intelligence_error']}")

            st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Advanced technical details"):
        tech_df = pd.DataFrame(
            [
                {"Internal feature": "hour", "Value": features["hour"]},
                {"Internal feature": "weekday", "Value": features["weekday"]},
                {"Internal feature": "is_weekend", "Value": features["is_weekend"]},
                {"Internal feature": "roll_mean_tts_10m", "Value": round(features["roll_mean_tts_10m"], 2)},
                {"Internal feature": "roll_max_tts_10m", "Value": round(features["roll_max_tts_10m"], 2)},
                {"Internal feature": "roll_count_10m", "Value": int(features["roll_count_10m"])},
                {"Internal feature": "baseline_median_tts", "Value": round(features["baseline_median_tts"], 2)},
                {"Internal feature": "deviation_from_baseline", "Value": round(features["deviation_from_baseline"], 2)},
            ]
        )
        st.dataframe(tech_df, use_container_width=True, hide_index=True)
        st.json(result)

else:
    st.markdown(
        """
        <div class="empty-box">
            <div style="font-size:3rem; margin-bottom:0.6rem;">🚇</div>
            <div style="font-size:1.2rem; font-weight:700; margin-bottom:0.35rem;">
                No monitoring data loaded yet
            </div>
            <div style="font-size:0.98rem;">
                Click <strong>Load Monitoring View</strong> to simulate multiple live arrivals,
                compare delay likelihoods across stations, and inspect one case in detail.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )