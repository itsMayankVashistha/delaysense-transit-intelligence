"""DelaySense operator dashboard.

A client of the DelaySense API. It holds no model and no feature logic: every
score, risk band and alert flag shown here comes from the backend.
"""

import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from app.ui import helpers as h
except ModuleNotFoundError:  # launched with the repo root off sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from app.ui import helpers as h

st.set_page_config(
    page_title="DelaySense",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"<style>{h.load_css()}</style>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Showcase demo payload
# --------------------------------------------------------------------------


def _demo(prob, risk, alert, explanation, display, feats):
    """Build one showcase arrival. Values are unchanged from the original set."""
    tts, roll_mean, roll_max, roll_count, baseline, deviation = feats
    return {
        "prob": prob,
        "risk": risk,
        "alert_flag": alert,
        "alert_mode": "Balanced",
        "alert_threshold": 0.60,
        "model_source": "showcase_demo",
        "model_info": {"model_name": "lightgbm_v2"},
        "explanation": explanation,
        "display": {
            "stop_id": display[0],
            "stop_name": display[1],
            "line_id": display[2],
            "direction": display[3],
            "platform_name": display[4],
            "destination_name": display[5],
            "vehicle_id": display[6],
            "observed_at": display[7],
        },
        "features": {
            "hour": 8,
            "weekday": 2,
            "is_weekend": 0,
            "time_to_station": tts,
            "roll_mean_tts_10m": roll_mean,
            "roll_max_tts_10m": roll_max,
            "roll_count_10m": roll_count,
            "baseline_median_tts": baseline,
            "deviation_from_baseline": deviation,
        },
    }


def build_showcase_demo_payload():
    results = [
        _demo(
            0.91, "high", True,
            "Current arrival estimate is 11m 20s, which is 5m 10s slower than the usual "
            "6m 10s. The system flags this as high delay risk.",
            ("940GZZLUOXC", "Oxford Circus Underground Station", "victoria", "outbound",
             "Northbound - Platform 6", "Walthamstow Central Underground Station",
             "showcase_001", 1772357400000),
            (680, 640, 720, 8, 370, 310),
        ),
        _demo(
            0.84, "high", True,
            "Current arrival estimate is 9m 45s, which is 4m 5s slower than the usual "
            "5m 40s. The system flags this as high delay risk.",
            ("940GZZLUWLO", "Waterloo Underground Station", "jubilee", "outbound",
             "Outbound Platform", "Stratford Underground Station",
             "showcase_002", 1772357460000),
            (585, 560, 620, 7, 340, 245),
        ),
        _demo(
            0.73, "high", True,
            "Current arrival estimate is 8m 15s, which is 3m 20s slower than the usual "
            "4m 55s. The system flags this as high delay risk.",
            ("940GZZLUGPK", "Green Park Underground Station", "victoria", "inbound",
             "Southbound Platform", "Brixton Underground Station",
             "showcase_003", 1772357520000),
            (495, 460, 520, 7, 295, 200),
        ),
        _demo(
            0.52, "medium", False,
            "Current arrival estimate is 6m 40s, which is 1m 55s slower than the usual "
            "4m 45s. The system detects elevated delay risk.",
            ("940GZZLUSTD", "Stratford Underground Station", "jubilee", "inbound",
             "Inbound Platform", "Stanmore Underground Station",
             "showcase_004", 1772357580000),
            (400, 380, 450, 6, 285, 115),
        ),
        _demo(
            0.44, "medium", False,
            "Current arrival estimate is 5m 30s, which is 1m 25s slower than the usual "
            "4m 5s. The system detects elevated delay risk.",
            ("940GZZLUWLO", "Waterloo Underground Station", "jubilee", "inbound",
             "Inbound Platform", "Stanmore Underground Station",
             "showcase_005", 1772357640000),
            (330, 310, 360, 6, 245, 85),
        ),
        _demo(
            0.36, "medium", False,
            "Current arrival estimate is 4m 50s, which is 1m 10s slower than the usual "
            "3m 40s. The system detects elevated delay risk.",
            ("940GZZLUBXN", "Brixton Underground Station", "victoria", "outbound",
             "Northbound Platform", "Walthamstow Central Underground Station",
             "showcase_006", 1772357700000),
            (290, 275, 320, 6, 220, 70),
        ),
        _demo(
            0.18, "low", False,
            "Current arrival estimate is 4m 2s, which is close to the usual 4m 10s. "
            "The system considers delay risk low.",
            ("940GZZLUOXC", "Oxford Circus Underground Station", "victoria", "inbound",
             "Southbound Platform", "Brixton Underground Station",
             "showcase_007", 1772357760000),
            (242, 250, 285, 5, 250, -8),
        ),
        _demo(
            0.11, "low", False,
            "Current arrival estimate is 3m 20s, which is 20s faster than the usual "
            "3m 40s. The system considers delay risk low.",
            ("940GZZLUGPK", "Green Park Underground Station", "victoria", "outbound",
             "Northbound Platform", "Walthamstow Central Underground Station",
             "showcase_008", 1772357820000),
            (200, 205, 240, 5, 220, -20),
        ),
        _demo(
            0.06, "low", False,
            "Current arrival estimate is 2m 35s, which is 35s faster than the usual "
            "3m 10s. The system considers delay risk low.",
            ("940GZZLUSTD", "Stratford Underground Station", "jubilee", "outbound",
             "Outbound Platform", "Stratford Underground Station",
             "showcase_009", 1772357880000),
            (155, 160, 190, 5, 190, -35),
        ),
    ]

    history = []
    for station, probs in (
        ("Oxford Circus Underground Station", [0.34, 0.49, 0.67, 0.84, 0.91]),
        ("Waterloo Underground Station", [0.28, 0.39, 0.55, 0.68, 0.84]),
        ("Green Park Underground Station", [0.12, 0.17, 0.26, 0.44, 0.73]),
    ):
        for minute, prob in zip(("25", "28", "31", "35", "40"), probs):
            history.append(
                {
                    "timestamp": f"2026-03-29T14:{minute}:00+00:00",
                    "uid": None,
                    "station": station,
                    "prob": prob,
                }
            )

    return {
        "source": "showcase_demo",
        "count": len(results),
        "results": results,
        "status": None,
        "history": history,
    }


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------


RISK_COLORS = {
    "HIGH": h.COLORS["high"],
    "MEDIUM": h.COLORS["medium"],
    "LOW": h.COLORS["low"],
}


def apply_plot_style(fig, height=250, margin=None, ygrid=True):
    fig.update_layout(
        paper_bgcolor=h.COLORS["transparent"],
        plot_bgcolor=h.COLORS["transparent"],
        margin=margin or dict(l=8, r=8, t=8, b=8),
        font=dict(color=h.COLORS["text_main"], size=12),
        showlegend=False,
        height=height,
        hoverlabel=dict(font_size=12),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, title=None, tickfont=dict(size=11))
    fig.update_yaxes(
        gridcolor=h.COLORS["grid"] if ygrid else "rgba(0,0,0,0)",
        zeroline=False,
        title=None,
        tickfont=dict(size=11),
    )
    return fig


def fig_current_vs_usual(current_sec, usual_sec, delta_sec, risk):
    """Compact horizontal comparison: current, usual and the difference."""
    frame = pd.DataFrame(
        {
            "Metric": ["Usual", "Current"],  # reversed so Current sits on top
            "Minutes": [usual_sec / 60.0, current_sec / 60.0],
            "Label": [
                h.format_seconds_human(usual_sec),
                h.format_seconds_human(current_sec),
            ],
        }
    )

    fig = px.bar(frame, x="Minutes", y="Metric", orientation="h", text="Label")
    fig.update_traces(
        marker_color=[h.COLORS["navy_light"], h.COLORS["navy"]],
        marker_line_width=0,
        textposition="outside",
        textfont=dict(size=12),
        cliponaxis=False,
        width=0.55,
        hovertemplate="%{y}: %{text}<extra></extra>",
    )

    upper = max(frame["Minutes"].max(), 0.1) * 1.34
    fig.update_xaxes(visible=False, range=[0, upper])
    fig.update_yaxes(showgrid=False, ticksuffix="  ", tickfont=dict(size=12))

    fig.add_annotation(
        x=1,
        y=1.32,
        xref="paper",
        yref="paper",
        xanchor="right",
        showarrow=False,
        text=f"<b>{h.format_delta_human(delta_sec)}</b> vs usual",
        font=dict(size=12, color=RISK_COLORS.get(str(risk).upper(), h.COLORS["text_soft"])),
    )

    return apply_plot_style(
        fig, height=132, margin=dict(l=8, r=8, t=26, b=4), ygrid=False
    )


def fig_arrival_trend(frame, threshold):
    """Risk over time with the alert threshold, shaded high-risk band and
    the latest observation highlighted."""
    fig = px.line(frame, x="ts", y="prob", markers=True)
    fig.update_traces(
        line=dict(width=2.5, color=h.COLORS["blue_soft"]),
        marker=dict(size=6, color=h.COLORS["blue_soft"]),
        hovertemplate="%{x|%H:%M}<br>Delay risk: %{y:.0%}<extra></extra>",
    )

    fig.add_hrect(
        y0=threshold,
        y1=1.0,
        fillcolor=h.COLORS["high"],
        opacity=0.07,
        line_width=0,
        layer="below",
    )
    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_width=1.5,
        line_color=h.COLORS["high"],
        annotation_text=f"Alert threshold {threshold:.0%}",
        annotation_position="top left",
        annotation_font=dict(size=10, color=h.COLORS["high"]),
    )

    latest = frame.iloc[-1]
    fig.add_scatter(
        x=[latest["ts"]],
        y=[float(latest["prob"])],
        mode="markers+text",
        marker=dict(
            size=13,
            color=h.COLORS["blue_soft"],
            line=dict(width=2.5, color="#ffffff"),
        ),
        text=[f"{float(latest['prob']):.0%}"],
        textposition="top center",
        textfont=dict(size=13, color=h.COLORS["text_main"]),
        hoverinfo="skip",
        showlegend=False,
    )

    fig.update_yaxes(range=[0, 1.1], tickformat=".0%", tickvals=[0, 0.5, 1])
    fig.update_xaxes(tickformat="%H:%M", nticks=5)
    return apply_plot_style(fig, height=248, margin=dict(l=8, r=16, t=16, b=8))


def fig_network_ranking(results):
    """One bar per arrival, ranked highest risk first, coloured by risk band."""
    frame = pd.DataFrame(
        {
            "Arrival": h.ranking_labels(results),
            "DelayRisk": [float(r.get("prob", 0.0)) for r in results],
            "Risk": [str(r.get("risk", "low")).upper() for r in results],
            "Difference": [
                h.format_delta_human((r.get("features") or {}).get("deviation_from_baseline", 0))
                for r in results
            ],
        }
    )
    # Ascending, so the highest risk renders at the top of a horizontal bar chart.
    frame = frame.sort_values("DelayRisk", ascending=True).reset_index(drop=True)

    fig = px.bar(frame, x="DelayRisk", y="Arrival", orientation="h", text="DelayRisk")
    fig.update_traces(
        marker_color=[RISK_COLORS.get(band, h.COLORS["navy_light"]) for band in frame["Risk"]],
        marker_line_width=0,
        texttemplate="%{x:.0%}",
        textposition="outside",
        textfont=dict(size=12),
        cliponaxis=False,
        customdata=np.stack([frame["Difference"], frame["Risk"]], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>Delay risk: %{x:.1%}<br>Risk band: %{customdata[1]}"
            "<br>Difference vs usual: %{customdata[0]}<extra></extra>"
        ),
    )

    fig.update_xaxes(visible=False, range=[0, 1.16])
    fig.update_yaxes(
        showgrid=False,
        automargin=True,  # keeps long station names from being clipped
        categoryorder="array",
        categoryarray=list(frame["Arrival"]),
        tickfont=dict(size=11),
    )
    return apply_plot_style(
        fig,
        height=max(220, 30 * len(frame) + 34),
        margin=dict(l=8, r=56, t=8, b=8),
        ygrid=False,
    )


# --------------------------------------------------------------------------
# Small render helpers
# --------------------------------------------------------------------------


def esc(value):
    """Escape backend-supplied text before it reaches an HTML block."""
    return html.escape(str(value), quote=True)


def kpi_card(label, value, sub, tone="blue"):
    st.markdown(
        f'<div class="ds-kpi {tone}">'
        f'<div class="ds-kpi-label">{esc(label)}</div>'
        f'<div class="ds-kpi-value">{esc(value)}</div>'
        f'<div class="ds-kpi-sub">{esc(sub)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def status_panel(title, detail="", tone="info"):
    """Compact status strip, used instead of the default Streamlit callouts."""
    detail_html = f'<div class="ds-status-detail">{esc(detail)}</div>' if detail else ""
    st.markdown(
        f'<div class="ds-status {tone}"><div class="ds-status-dot"></div><div>'
        f'<div class="ds-status-title">{esc(title)}</div>{detail_html}'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def section(title, note=None):
    st.markdown(f'<div class="ds-section">{esc(title)}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(
            f'<div class="ds-section-note">{esc(note)}</div>', unsafe_allow_html=True
        )


def render_hero():
    """Render the banner whole and uncropped.

    The artwork already carries the wordmark, tagline, value proposition and
    feature chips, so no text overlay is drawn on top of it. Streamlit serves
    the file from its media endpoint rather than inlining it in the page.
    """
    if h.HERO_PATH.exists():
        st.image(str(h.HERO_PATH), width="stretch")
    else:
        st.markdown(
            '<div class="ds-hero-fallback">'
            '<div class="ds-hero-fallback-title">DelaySense</div>'
            '<div class="ds-hero-fallback-sub">Transit intelligence — real-time early '
            "warning for London Underground arrivals</div></div>",
            unsafe_allow_html=True,
        )


def render_priority_card(rank, result):
    display = result.get("display") or {}
    features = result.get("features") or {}
    prob = float(result.get("prob", 0.0))
    risk = h.risk_tone(result.get("risk"))

    st.markdown(
        f'<div class="ds-prio {risk}">'
        f'<div class="ds-prio-rank">Priority {rank}</div>'
        f'<div class="ds-prio-title">{esc(display.get("stop_name", "Unknown"))} → '
        f'{esc(display.get("destination_name", "Unknown"))}</div>'
        f'<div class="ds-prio-metrics">'
        f'<div><div class="ds-prio-metric-label">Delay risk</div>'
        f'<div class="ds-prio-metric-value">{prob:.0%}</div></div>'
        f'<div><div class="ds-prio-metric-label">Vs usual</div>'
        f'<div class="ds-prio-metric-value">'
        f'{esc(h.format_delta_human(features.get("deviation_from_baseline", 0)))}'
        f"</div></div></div>"
        f'<div class="ds-prio-action">{esc(h.action_text_from_risk(result.get("risk")))}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------


def load_source(source, force_refresh=False):
    """Return (payload, error) for the requested monitoring source."""
    if source == "Live TfL":
        if force_refresh:
            with st.spinner(f"Requesting a fresh poll from the backend… {h.WAKING_HINT}"):
                return h.refresh_live_monitoring()
        with st.spinner(f"Loading the live monitor… {h.WAKING_HINT}"):
            return h.fetch_live_monitoring()
    return build_showcase_demo_payload(), None


def store_payload(payload, source):
    results = h.assign_arrival_uids(list(payload.get("results") or []))
    if not results:
        return False

    status = payload.get("status")
    st.session_state.update(
        {
            "monitor_results": results,
            "monitor_df": h.build_monitoring_table(results),
            "monitor_source": payload.get("source", "unknown"),
            "monitor_status": status,
            "data_source": source,
        }
    )

    if source == "Live TfL":
        st.session_state["live_history"] = h.append_live_history(
            st.session_state.get("live_history", []), results, status
        )
    else:
        st.session_state["showcase_history"] = payload.get("history", [])

    selected = st.session_state.get("selected_uid")
    if not any(r["_uid"] == selected for r in results):
        st.session_state["selected_uid"] = results[0]["_uid"]

    return True


# --------------------------------------------------------------------------
# Header and controls
# --------------------------------------------------------------------------

render_hero()

health, health_error = h.fetch_health()

with st.container(border=True):
    control_cols = st.columns([1.5, 1, 1])

    with control_cols[0]:
        data_source = st.radio(
            "Monitoring source",
            ["Showcase demo", "Live TfL"],
            index=0 if st.session_state.get("data_source", "Showcase demo") == "Showcase demo" else 1,
            horizontal=True,
            help=(
                "Showcase demo uses a curated, deterministic set of arrivals. "
                "Live TfL reads the current state of the backend monitor."
            ),
        )

    with control_cols[1]:
        st.markdown('<div style="height:1.7rem"></div>', unsafe_allow_html=True)
        load_clicked = st.button("Load data", width="stretch", type="primary")

    with control_cols[2]:
        st.markdown('<div style="height:1.7rem"></div>', unsafe_allow_html=True)
        refresh_clicked = st.button(
            "Refresh live data",
            width="stretch",
            disabled=data_source != "Live TfL",
            help="Forces a new backend poll. Available in Live TfL mode only.",
        )

    active_mode = h.active_alert_mode(health)
    if active_mode:
        st.caption(
            f"Alert mode: **{active_mode}** — applied by the backend monitor and shown "
            "here for reference. It is not configurable from the dashboard."
        )

# First visit: load the offline showcase set so the dashboard is never empty.
if "monitor_results" not in st.session_state and not (load_clicked or refresh_clicked):
    store_payload(build_showcase_demo_payload(), "Showcase demo")
    st.session_state["data_source"] = "Showcase demo"

if load_clicked or refresh_clicked:
    payload, load_error = load_source(data_source, force_refresh=refresh_clicked)
    if load_error:
        status_panel("Backend unavailable", load_error, tone="error")
    elif payload is None or not store_payload(payload, data_source):
        status_panel(
            "No arrivals returned",
            "The live monitor may still be warming up. Try again in a moment, or "
            "switch to the showcase demo.",
            tone="warn",
        )

monitor_results = st.session_state.get("monitor_results")
monitor_df = st.session_state.get("monitor_df")
monitor_status = st.session_state.get("monitor_status")
source_label = str(st.session_state.get("monitor_source", "unknown"))
is_live = source_label.startswith("tfl_live")

if health_error:
    status_panel("System status unavailable", health_error, tone="warn")

if not monitor_results:
    st.markdown(
        '<div class="ds-empty">No arrivals loaded yet. Choose a monitoring source '
        "above and select <strong>Load data</strong>.</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# --------------------------------------------------------------------------
# Summary cards
# --------------------------------------------------------------------------

probs = [float(r.get("prob", 0.0)) for r in monitor_results]
avg_prob = float(np.mean(probs)) if probs else 0.0
network_label = h.overall_risk_label(avg_prob)
high_risk_count = sum(1 for r in monitor_results if str(r.get("risk", "")).lower() == "high")
alert_count = sum(1 for r in monitor_results if r.get("alert_flag"))

if is_live:
    engine = h.format_model_name((health or {}).get("model_info"))
    source_note = "Live monitor feed"
else:
    engine = "Showcase demo"
    source_note = "Curated showcase set"

kpi_cols = st.columns(4)
with kpi_cols[0]:
    kpi_card(
        "Network condition",
        f"{network_label} · {avg_prob:.0%}",
        "Average delay risk across monitored arrivals",
        tone={"High": "red", "Medium": "amber"}.get(network_label, "green"),
    )
with kpi_cols[1]:
    kpi_card(
        "High-risk arrivals",
        str(high_risk_count),
        f"{alert_count} above the alert threshold",
        tone="red" if high_risk_count else "green",
    )
with kpi_cols[2]:
    kpi_card("Monitored arrivals", str(len(monitor_results)), source_note)
with kpi_cols[3]:
    if health:
        kpi_card("System status", "Online", f"Engine: {engine}", tone="green")
    else:
        kpi_card("System status", "Offline", "Backend unreachable", tone="red")

if is_live and monitor_status:
    st.caption(
        f"Monitor {'running' if monitor_status.get('is_running') else 'stopped'} · "
        f"polling every {monitor_status.get('poll_interval_seconds', '—')}s · "
        f"{h.monitor_readiness_text(monitor_status)} · last update "
        f"{h.format_network_time(monitor_status.get('last_success_at'))} London time"
    )


# --------------------------------------------------------------------------
# Priority alerts
# --------------------------------------------------------------------------

with st.container(border=True):
    section("Priority alerts", "The three highest-risk arrivals across the whole monitored set.")
    priority = h.get_priority_results(monitor_results, top_n=3)
    priority_cols = st.columns(max(len(priority), 1))
    for idx, result in enumerate(priority):
        with priority_cols[idx]:
            render_priority_card(idx + 1, result)


# --------------------------------------------------------------------------
# Monitored arrivals table
# --------------------------------------------------------------------------

with st.container(border=True):
    section("Monitored arrivals", "Filter the set, then sort any column.")

    filter_cols = st.columns(3)
    with filter_cols[0]:
        lines = sorted({row for row in monitor_df["Line"] if row})
        line_filter = st.multiselect("Line", lines, default=[], placeholder="All lines")
    with filter_cols[1]:
        stations = sorted({row for row in monitor_df["Station"] if row})
        station_filter = st.multiselect(
            "Station", stations, default=[], placeholder="All stations"
        )
    with filter_cols[2]:
        risk_options = ["High", "Medium", "Low"]
        risk_filter = st.multiselect(
            "Risk level", risk_options, default=[], placeholder="All risk levels"
        )

    filtered_df = monitor_df
    if line_filter:
        filtered_df = filtered_df[filtered_df["Line"].isin(line_filter)]
    if station_filter:
        filtered_df = filtered_df[filtered_df["Station"].isin(station_filter)]
    if risk_filter:
        wanted = {f"{h.RISK_ICONS[r.upper()]} {r}" for r in risk_filter}
        filtered_df = filtered_df[filtered_df["Risk"].isin(wanted)]

    if filtered_df.empty:
        st.info("No arrivals match the current filters.")
    else:
        st.dataframe(
            filtered_df,
            column_config=h.MONITOR_COLUMN_CONFIG,
            hide_index=True,
            width="stretch",
        )
        st.caption(f"Showing {len(filtered_df)} of {len(monitor_df)} monitored arrivals.")


# --------------------------------------------------------------------------
# Selected arrival analysis
# --------------------------------------------------------------------------

visible_uids = set(filtered_df["_uid"]) if not filtered_df.empty else set()
selectable = [r for r in monitor_results if r["_uid"] in visible_uids] or monitor_results

uid_options = [r["_uid"] for r in selectable]
stored_uid = st.session_state.get("selected_uid")
default_index = uid_options.index(stored_uid) if stored_uid in uid_options else 0
label_lookup = {r["_uid"]: h.arrival_label(r) for r in selectable}

with st.container(border=True):
    section("Selected arrival", "Arrivals are identified individually, so two trains at the same station stay distinct.")

    selected_uid = st.selectbox(
        "Arrival",
        uid_options,
        index=default_index,
        format_func=lambda uid: label_lookup.get(uid, uid),
    )
    st.session_state["selected_uid"] = selected_uid

    result = h.find_arrival(selectable, selected_uid)
    if result is None:
        st.info("This arrival is no longer available. Load data again to refresh the set.")
        st.stop()

    display = result.get("display") or {}
    features = result.get("features") or {}
    prob = float(result.get("prob", 0.0))
    risk = h.risk_tone(result.get("risk"))
    current_sec = float(features.get("time_to_station", 0) or 0)
    usual_sec = float(features.get("baseline_median_tts", 0) or 0)
    delta_sec = float(features.get("deviation_from_baseline", 0) or 0)
    threshold = float(result.get("alert_threshold") or 0.60)
    source_display = "Live TfL" if is_live else "Showcase demo"

    detail_col, trend_col = st.columns([1, 1])

    with detail_col:
        st.markdown(
            f'<div class="ds-banner {risk}">'
            f'<div class="ds-banner-kicker">Selected arrival</div>'
            f'<div class="ds-banner-headline">{esc(str(result.get("risk", "")).upper())} RISK '
            f'— {esc(h.action_text_from_risk(result.get("risk")))}</div>'
            f'<div class="ds-banner-route">{esc(display.get("stop_name", "Unknown station"))} → '
            f'{esc(display.get("destination_name", "Unknown destination"))}</div>'
            f'<div class="ds-banner-meta">'
            f"<span>Delay risk <strong>{prob:.1%}</strong></span>"
            f'<span>Alert <strong>{"Yes" if result.get("alert_flag") else "No"}</strong></span>'
            f"<span>Engine <strong>{esc(engine)}</strong></span>"
            f"<span>Source <strong>{esc(source_display)}</strong></span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        st.plotly_chart(
            fig_current_vs_usual(current_sec, usual_sec, delta_sec, result.get("risk")),
            width="stretch",
        )

        st.markdown(
            '<div class="ds-pills">'
            f'<div class="ds-pill"><div class="ds-pill-label">Condition</div>'
            f'<div class="ds-pill-value">{esc(h.micro_hint(features))}</div></div>'
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="ds-explain" style="margin-top:0.65rem;">'
            f"{esc(h.explanation_text(result))}<br><br>"
            f"<strong>Recommendation:</strong> {esc(h.action_sentence(result))}</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="ds-meta-line">'
            f'<span>Line: <strong>{esc(str(display.get("line_id", "")).title())}</strong></span>'
            f'<span>Direction: <strong>{esc(str(display.get("direction") or "—").title())}</strong></span>'
            f'<span>Platform: <strong>{esc(display.get("platform_name", "Unknown"))}</strong></span>'
            "</div>",
            unsafe_allow_html=True,
        )

    with trend_col:
        section("Risk trend")
        history = (
            st.session_state.get("live_history", [])
            if is_live
            else st.session_state.get("showcase_history", [])
        )
        trend_frame = h.arrival_history_frame(history, selected_uid, display.get("stop_name"))

        if trend_frame is not None:
            st.plotly_chart(fig_arrival_trend(trend_frame, threshold), width="stretch")
            st.markdown(
                f'<div class="ds-explain">{esc(h.trend_summary(trend_frame, threshold))}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="ds-empty" style="padding:1.6rem 1rem;">'
                "A trend appears once this arrival has been observed more than once."
                "</div>",
                unsafe_allow_html=True,
            )

with st.container(border=True):
    section("Network risk ranking", "All monitored arrivals, highest delay risk first.")
    st.plotly_chart(fig_network_ranking(monitor_results), width="stretch")


# --------------------------------------------------------------------------
# Technical details
# --------------------------------------------------------------------------

with st.expander("Technical details — raw prediction, features and model metadata"):
    intelligence = result.get("intelligence")
    if intelligence:
        summary = intelligence.get("summary") or intelligence.get("narrative")
        if summary:
            st.markdown("**Additional context**")
            st.markdown(f'<div class="ds-explain">{esc(summary)}</div>', unsafe_allow_html=True)
        similar = intelligence.get("similar_cases")
        if similar:
            st.markdown("**Similar historical cases**")
            st.dataframe(pd.DataFrame(similar), hide_index=True, width="stretch")

    st.markdown("**Selected arrival payload**")
    st.code(json.dumps(h.strip_internal_keys(result), indent=2), language="json")

    st.markdown("**Backend health**")
    st.code(json.dumps(health or {"error": health_error}, indent=2), language="json")
