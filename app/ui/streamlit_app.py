import requests
import pandas as pd
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="TfL Delay Intelligence",
    page_icon="🚇",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .hero-card {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 1.4rem 1.5rem;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .hero-subtitle {
        font-size: 1rem;
        color: #cbd5e1;
        margin-bottom: 0.25rem;
    }

    .soft-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 1rem 1rem 0.9rem 1rem;
        color: white;
        box-shadow: 0 8px 20px rgba(0,0,0,0.18);
        height: 100%;
    }

    .metric-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        color: white;
        box-shadow: 0 8px 18px rgba(0,0,0,0.18);
        min-height: 120px;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-bottom: 0.35rem;
    }

    .metric-value {
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.2;
    }

    .metric-sub {
        font-size: 0.9rem;
        color: #cbd5e1;
        margin-top: 0.35rem;
    }

    .risk-banner {
        padding: 1.2rem 1.2rem 1rem 1.2rem;
        border-radius: 18px;
        color: white;
        box-shadow: 0 10px 28px rgba(0,0,0,0.22);
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.08);
    }

    .risk-low {
        background: linear-gradient(135deg, #166534 0%, #15803d 100%);
    }

    .risk-medium {
        background: linear-gradient(135deg, #b45309 0%, #d97706 100%);
    }

    .risk-high {
        background: linear-gradient(135deg, #991b1b 0%, #dc2626 100%);
    }

    .pill {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-top: 0.3rem;
        color: white;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.12);
    }

    .section-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 1rem 1rem 0.8rem 1rem;
        color: white;
        box-shadow: 0 8px 20px rgba(0,0,0,0.18);
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.08rem;
        font-weight: 700;
        margin-bottom: 0.7rem;
    }

    .small-muted {
        color: #94a3b8;
        font-size: 0.88rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 0.9rem 1rem;
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_metric_card(label: str, value: str, sub: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def fetch_health():
    response = requests.get(f"{API_URL}/health", timeout=5)
    response.raise_for_status()
    return response.json()


def predict_sample(selected_mode: str, include_intelligence: bool):
    payload = {
        "observed_at": 1772357400000,
        "stop_id": "940GZZLUOXC",
        "stop_name": "Oxford Circus",
        "line_id": "victoria",
        "vehicle_id": "demo_vehicle_001",
        "direction": "northbound",
        "platform_name": "Northbound Platform",
        "destination_name": "Walthamstow Central",
        "time_to_station": 660,
        "alert_mode": selected_mode,
        "include_intelligence": include_intelligence,
    }

    response = requests.post(
        f"{API_URL}/predict",
        json=payload,
        timeout=8,
    )
    response.raise_for_status()
    return response.json()


def build_overview_table(result: dict) -> pd.DataFrame:
    display = result["display"]
    features = result["features"]

    return pd.DataFrame(
        [
            {
                "Station": display["stop_name"],
                "Line": display["line_id"].title(),
                "Direction": display["direction"].title(),
                "Platform": display["platform_name"],
                "Destination": display["destination_name"],
                "Current ETA (min)": round(features["time_to_station"] / 60, 2),
                "Typical ETA (min)": round(features["baseline_median_tts"] / 60, 2),
                "Difference (min)": round(features["deviation_from_baseline"] / 60, 2),
                "Risk": result["risk"].upper(),
                "Alert": "YES" if result["alert_flag"] else "NO",
                "Probability": round(result["prob"], 3),
            }
        ]
    )


st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">🚇 TfL Delay Intelligence</div>
        <div class="hero-subtitle">Real-time delay early-warning demo for Victoria and Jubilee line arrivals</div>
        <div class="small-muted">Path B forecasting interface • mock/joblib compatible • intelligence-ready</div>
    </div>
    """,
    unsafe_allow_html=True,
)

left_top, right_top = st.columns([1.2, 1])

with left_top:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Controls</div>', unsafe_allow_html=True)

    selected_mode = st.radio(
        "Alert sensitivity",
        ["Conservative", "Balanced", "Sensitive"],
        index=1,
        horizontal=True,
    )

    include_intelligence = st.checkbox(
        "Enable intelligence layer",
        value=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        check_api = st.button("Check API", use_container_width=True)
    with c2:
        load_prediction = st.button("Load Sample Prediction", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

with right_top:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">System Summary</div>', unsafe_allow_html=True)

    health_data = None
    health_error = None

    try:
        health_data = fetch_health()
    except Exception as e:
        health_error = str(e)

    s1, s2 = st.columns(2)
    with s1:
        if health_data:
            render_metric_card("API", "Online", "Backend reachable")
        else:
            render_metric_card("API", "Offline", "Backend unreachable")

    with s2:
        render_metric_card("Mode", selected_mode, "Active alert profile")

    s3, s4 = st.columns(2)
    with s3:
        model_source = health_data.get("model_source", "unknown") if health_data else "unknown"
        render_metric_card("Model Source", str(model_source), "Current inference backend")

    with s4:
        intel_enabled = health_data.get("intelligence_enabled", False) if health_data else False
        render_metric_card("Intelligence", "On" if intel_enabled else "Off", "Enrichment layer status")

    if check_api:
        if health_data:
            st.success("API reachable")
            st.json(health_data)
        else:
            st.error(f"API not reachable: {health_error}")

    st.markdown('</div>', unsafe_allow_html=True)

result = None
prediction_error = None

if load_prediction:
    try:
        result = predict_sample(selected_mode, include_intelligence)
        st.session_state["latest_result"] = result
    except Exception as e:
        prediction_error = str(e)

if "latest_result" in st.session_state and result is None:
    result = st.session_state["latest_result"]

if prediction_error:
    st.error(f"Prediction failed: {prediction_error}")

if result:
    display = result["display"]
    features = result["features"]
    prob = result["prob"]
    risk = result["risk"]
    explanation = result["explanation"]
    alert_flag = result["alert_flag"]
    model_source = result.get("model_source", "unknown")

    risk_class = f"risk-{risk}"

    st.markdown(
        f"""
        <div class="risk-banner {risk_class}">
            <div style="font-size:1.5rem;font-weight:800;margin-bottom:0.2rem;">
                {display['stop_name']} • {display['line_id'].title()}
            </div>
            <div style="font-size:1rem;opacity:0.95;margin-bottom:0.6rem;">
                {display['direction'].title()} • {display['platform_name']} • Destination: {display['destination_name']}
            </div>
            <div style="font-size:2rem;font-weight:800;line-height:1.1;">
                {risk.upper()} RISK
            </div>
            <div style="margin-top:0.5rem;font-size:1rem;">
                Probability: <strong>{prob:.3f}</strong> &nbsp; | &nbsp;
                Alert: <strong>{"YES" if alert_flag else "NO"}</strong> &nbsp; | &nbsp;
                Mode: <strong>{selected_mode}</strong> &nbsp; | &nbsp;
                Model: <strong>{model_source}</strong>
            </div>
            <div>
                <span class="pill">Vehicle: {display.get('vehicle_id', 'N/A')}</span>
                <span class="pill">Forecast target: future delay</span>
                <span class="pill">Context-aware baseline</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    row1 = st.columns(4)
    with row1[0]:
        st.metric("Current ETA", f"{features['time_to_station']/60:.1f} min")
    with row1[1]:
        st.metric("Typical ETA", f"{features['baseline_median_tts']/60:.1f} min")
    with row1[2]:
        st.metric("Difference", f"{features['deviation_from_baseline']/60:.1f} min")
    with row1[3]:
        st.metric("Rolling Count", f"{int(features['roll_count_10m'])}")

    left_main, right_main = st.columns([1.15, 0.85])

    with left_main:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Operational Explanation</div>', unsafe_allow_html=True)
        st.info(explanation)

        overview_df = build_overview_table(result)
        st.markdown('<div class="section-title">Arrival Snapshot</div>', unsafe_allow_html=True)
        st.dataframe(overview_df, use_container_width=True, hide_index=True)

        comparison_df = pd.DataFrame(
            {
                "Measure": ["Typical ETA", "Current ETA"],
                "Minutes": [
                    features["baseline_median_tts"] / 60,
                    features["time_to_station"] / 60,
                ],
            }
        ).set_index("Measure")

        st.markdown('<div class="section-title">Current vs Typical</div>', unsafe_allow_html=True)
        st.bar_chart(comparison_df)

        rolling_df = pd.DataFrame(
            {
                "Metric": ["Rolling Mean", "Rolling Max", "Current"],
                "Minutes": [
                    features["roll_mean_tts_10m"] / 60,
                    features["roll_max_tts_10m"] / 60,
                    features["time_to_station"] / 60,
                ],
            }
        ).set_index("Metric")

        st.markdown('<div class="section-title">Recent Rolling Context</div>', unsafe_allow_html=True)
        st.bar_chart(rolling_df)

        st.markdown('</div>', unsafe_allow_html=True)

    with right_main:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Risk Breakdown</div>', unsafe_allow_html=True)

        threshold_value = 0.80 if selected_mode == "Conservative" else 0.60 if selected_mode == "Balanced" else 0.40

        gauge_df = pd.DataFrame(
            {
                "Category": ["Probability", "Alert Threshold"],
                "Value": [
                    prob,
                    threshold_value,
                ],
            }
        ).set_index("Category")
        st.bar_chart(gauge_df)

        detail_df = pd.DataFrame(
            [
                {"Feature": "Hour", "Value": features["hour"]},
                {"Feature": "Weekday", "Value": features["weekday"]},
                {"Feature": "Weekend", "Value": features["is_weekend"]},
                {"Feature": "Rolling mean (min)", "Value": round(features["roll_mean_tts_10m"] / 60, 2)},
                {"Feature": "Rolling max (min)", "Value": round(features["roll_max_tts_10m"] / 60, 2)},
                {"Feature": "Deviation (min)", "Value": round(features["deviation_from_baseline"] / 60, 2)},
            ]
        )
        st.markdown('<div class="section-title">Feature Snapshot</div>', unsafe_allow_html=True)
        st.dataframe(detail_df, use_container_width=True, hide_index=True)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Intelligence Layer</div>', unsafe_allow_html=True)

        if "intelligence" in result:
            intel = result["intelligence"]

            summary = intel.get("summary")
            if summary:
                st.write(summary)

            baseline_block = intel.get("baseline")
            if baseline_block:
                st.markdown("**Baseline comparison**")
                st.json(baseline_block)

            rolling_block = intel.get("rolling")
            if rolling_block:
                st.markdown("**Rolling behaviour**")
                st.json(rolling_block)

            similar_cases = intel.get("similar_cases")
            if similar_cases:
                st.markdown("**Similar historical cases**")
                st.json(similar_cases)
        else:
            st.write("No intelligence output available for this request.")

        if "intelligence_error" in result:
            st.warning(f"Intelligence layer error: {result['intelligence_error']}")

        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Technical Details"):
        st.json(result)

else:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">No active prediction yet</div>
            <div class="small-muted">
                Use <strong>Load Sample Prediction</strong> to fetch a full API response,
                evaluate the selected alert mode, and render the dashboard.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )