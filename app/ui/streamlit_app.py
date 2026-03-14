import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="TfL Delay Intelligence",
    page_icon="🚇",
    layout="wide",
)

st.markdown("""
    <style>
    .main {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        color: white;
    }
    .risk-card {
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
    }
    .low-risk {
        border-left: 8px solid #22c55e;
    }
    .medium-risk {
        border-left: 8px solid #f59e0b;
    }
    .high-risk {
        border-left: 8px solid #ef4444;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚇 TfL Delay Intelligence")
st.caption("Real-time transit delay anomaly detection demo")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Backend")
    if st.button("Check API Health"):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            st.success(response.json())
        except Exception as e:
            st.error(f"API call failed: {e}")

with col2:
    st.subheader("Demo Prediction")
    if st.button("Load Sample Prediction"):
        try:
            response = requests.get(f"{API_URL}/sample", timeout=5)
            result = response.json()

            display = result["display"]
            features = result["features"]
            prob = result["prob"]
            risk = result["risk"]
            explanation = result["explanation"]

            risk_class = f"{risk}-risk"

            st.markdown(
                f"""
                <div class="risk-card {risk_class}">
                    <h3 style="margin-bottom:0.25rem;">{display['stop_name']}</h3>
                    <p style="margin-top:0;">Line: {display['line_id'].title()} | Direction: {display['direction'].title()}</p>
                    <p>Platform: {display['platform_name']}</p>
                    <p>Destination: {display['destination_name']}</p>
                    <h2 style="margin-top:1rem;">Risk: {risk.title()}</h2>
                    <p>Probability: {prob:.3f}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            m1, m2, m3 = st.columns(3)
            m1.metric("Current estimate", f"{features['time_to_station']/60:.1f} min")
            m2.metric("Typical estimate", f"{features['baseline_median_tts']/60:.1f} min")
            m3.metric("Difference", f"{(features['time_to_station'] - features['baseline_median_tts'])/60:.1f} min")

            st.subheader("Explanation")
            st.info(explanation)

            st.subheader("Visual comparison")
            chart_df = pd.DataFrame({
                "Type": ["Typical", "Current"],
                "Minutes": [
                    features["baseline_median_tts"] / 60,
                    features["time_to_station"] / 60,
                ]
            }).set_index("Type")
            st.bar_chart(chart_df)

            with st.expander("Technical details"):
                st.json(result)

        except Exception as e:
            st.error(f"Prediction failed: {e}")