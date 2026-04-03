"""
=============================================================
MILESTONE 4: Streamlit Dashboard for Insights (Weeks 7-8)
=============================================================
- Interactive UI: file upload, anomaly detection trigger
- Filter by date range and metric
- Visualize anomalies dynamically
- Export reports (CSV/PDF summary)

Run with:  streamlit run modules/milestone4_dashboard.py
=============================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
import io
import sys

# ── Add parent dir so modules can be imported ──
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.milestone1_preprocessing import (
    normalize_timestamps, handle_missing_values, resample_data
)
from modules.milestone3_anomaly import (
    rule_based_detection, compute_anomaly_score
)

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FitPulse — Health Anomaly Detection",
    page_icon="💓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem; font-weight: 700;
        background: linear-gradient(90deg, #E74C3C, #9B59B6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: #1a1a2e; border-radius: 12px; padding: 18px;
        text-align: center; border: 1px solid #2d2d44;
    }
    .alert-high   { background: #4a1010; border-left: 4px solid #E74C3C; padding: 10px; border-radius: 8px; }
    .alert-medium { background: #4a3010; border-left: 4px solid #E67E22; padding: 10px; border-radius: 8px; }
    .alert-low    { background: #1a3a10; border-left: 4px solid #2ECC71; padding: 10px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helper: Load Data
# ─────────────────────────────────────────────
@st.cache_data
def load_and_process(file_bytes, file_name):
    ext = os.path.splitext(file_name)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(io.BytesIO(file_bytes))
    elif ext == ".json":
        raw = json.loads(file_bytes)
        df = pd.DataFrame(raw if isinstance(raw, list) else [raw])
    else:
        return None, "Unsupported format. Upload CSV or JSON."

    try:
        df_norm = normalize_timestamps(df)
        df_clean = handle_missing_values(df_norm)
        df_resampled = resample_data(df_clean, freq="5min")
        df_result = rule_based_detection(df_resampled)
        df_result["prophet_anomaly"] = 0
        df_result["dbscan_anomaly"] = 0
        df_result = compute_anomaly_score(df_result)
        return df_result, None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────
# Plotly Chart Helpers
# ─────────────────────────────────────────────
def plot_metric(df, metric, label, color, threshold_high=None, threshold_low=None):
    fig = go.Figure()

    # Main line
    fig.add_trace(go.Scatter(
        x=df.index, y=df[metric],
        mode="lines", name=label,
        line=dict(color=color, width=1),
        opacity=0.7,
    ))

    # Anomaly scatter
    anomaly_df = df[df["final_anomaly"] == 1]
    sev_color = {"low": "#F39C12", "medium": "#E67E22", "high": "#C0392B"}
    for sev, sc in sev_color.items():
        mask = anomaly_df["severity"] == sev
        if mask.any():
            fig.add_trace(go.Scatter(
                x=anomaly_df.index[mask], y=anomaly_df[metric][mask],
                mode="markers", name=f"Anomaly ({sev})",
                marker=dict(color=sc, size=7, symbol="x"),
            ))

    if threshold_high:
        fig.add_hline(y=threshold_high, line_dash="dash", line_color="red",
                      annotation_text=f"High threshold ({threshold_high})")
    if threshold_low:
        fig.add_hline(y=threshold_low, line_dash="dash", line_color="orange",
                      annotation_text=f"Low threshold ({threshold_low})")

    fig.update_layout(
        title=f"{label} with Anomaly Markers",
        xaxis_title="Time", yaxis_title=label,
        height=350, template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def plot_daily_anomaly_rate(df):
    df2 = df.copy()
    df2["date"] = df2.index.date
    daily = df2.groupby("date").agg(
        anomalies=("final_anomaly", "sum"),
        total=("final_anomaly", "count"),
    ).reset_index()
    daily["rate"] = (daily["anomalies"] / daily["total"] * 100).round(2)

    fig = px.bar(daily, x="date", y="rate",
                 color="rate",
                 color_continuous_scale=["#2ECC71", "#F39C12", "#E74C3C"],
                 labels={"rate": "Anomaly Rate (%)", "date": "Date"},
                 title="Daily Anomaly Rate (%)")
    fig.update_layout(height=300, template="plotly_dark",
                      coloraxis_showscale=False,
                      margin=dict(l=40, r=20, t=50, b=40))
    return fig


def plot_anomaly_type_pie(df):
    rule_cols = {
        "Tachycardia": "rule_tachycardia",
        "Bradycardia": "rule_bradycardia",
        "Low SpO2":    "rule_low_spo2",
        "Sleep Steps": "rule_sleep_steps",
        "Sleep HR":    "rule_sleep_hr",
    }
    counts = {label: int(df[col].sum()) for label, col in rule_cols.items() if col in df.columns}
    counts = {k: v for k, v in counts.items() if v > 0}
    if not counts:
        return None

    fig = px.pie(
        names=list(counts.keys()), values=list(counts.values()),
        title="Anomaly Type Distribution",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig.update_layout(height=300, template="plotly_dark",
                      margin=dict(l=20, r=20, t=50, b=20))
    return fig


# ─────────────────────────────────────────────
# Export Report
# ─────────────────────────────────────────────
def generate_csv_report(df):
    anomalies = df[df["final_anomaly"] == 1].copy()
    rule_cols = ["rule_tachycardia", "rule_bradycardia", "rule_low_spo2",
                 "rule_sleep_steps", "rule_sleep_hr"]
    cols = ["heart_rate_bpm", "steps", "spo2_pct", "severity", "anomaly_score"] + \
           [c for c in rule_cols if c in anomalies.columns]
    return anomalies[cols].to_csv().encode("utf-8")


def generate_summary_report(df):
    total = len(df)
    n_anomaly = int(df["final_anomaly"].sum())
    lines = [
        "=" * 50,
        "     FITPULSE HEALTH ANOMALY REPORT",
        "=" * 50,
        f"Period           : {df.index.min().date()} → {df.index.max().date()}",
        f"Total Readings   : {total}",
        f"Anomalies Found  : {n_anomaly} ({n_anomaly/total*100:.2f}%)",
        "",
        "── Severity Breakdown ──",
    ]
    for sev in ["high", "medium", "low"]:
        count = int((df["severity"] == sev).sum())
        lines.append(f"  {sev.capitalize():8s}: {count}")

    lines += [
        "",
        "── Anomaly Types ──",
    ]
    rule_map = {
        "Tachycardia (HR > 120)": "rule_tachycardia",
        "Bradycardia (HR < 45)":  "rule_bradycardia",
        "Low SpO2 (< 94%)":       "rule_low_spo2",
        "Steps during sleep":     "rule_sleep_steps",
        "High HR during sleep":   "rule_sleep_hr",
    }
    for label, col in rule_map.items():
        if col in df.columns:
            lines.append(f"  {label:30s}: {int(df[col].sum())}")

    lines += [
        "",
        "── Metric Averages ──",
        f"  Avg Heart Rate : {df['heart_rate_bpm'].mean():.1f} bpm",
        f"  Avg SpO2       : {df['spo2_pct'].mean():.1f} %",
        f"  Total Steps    : {int(df['steps'].sum())}",
        "=" * 50,
    ]
    return "\n".join(lines).encode("utf-8")


# ─────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────
def main():
    # ── Header ──
    st.markdown('<p class="main-header">💓 FitPulse — Health Anomaly Detection</p>', unsafe_allow_html=True)
    st.markdown("Upload your fitness watch data (CSV/JSON) to detect health anomalies automatically.")
    st.divider()

    # ── Sidebar ──
    with st.sidebar:
        st.header("⚙️ Configuration")
        uploaded_file = st.file_uploader(
            "📂 Upload Fitness Data", type=["csv", "json"],
            help="CSV/JSON from your fitness device. Must include: timestamp, heart_rate_bpm, steps, spo2_pct"
        )

        st.subheader("🔧 Thresholds")
        hr_high = st.slider("Tachycardia HR threshold (bpm)", 100, 150, 120)
        hr_low  = st.slider("Bradycardia HR threshold (bpm)", 30, 60, 45)
        spo2_low = st.slider("Low SpO2 threshold (%)", 85, 96, 94)

        st.subheader("📅 Date Filter")
        use_demo = st.checkbox("Use demo dataset", value=uploaded_file is None)

        st.markdown("---")
        st.caption("FitPulse Health Monitor v1.0")

    # ── Load Data ──
    df = None
    if use_demo and os.path.exists("outputs/anomaly_results.csv"):
        df = pd.read_csv("outputs/anomaly_results.csv", index_col=0, parse_dates=True)
        st.info("📊 Using pre-processed demo dataset (60 days)")
    elif uploaded_file:
        with st.spinner("Processing your fitness data..."):
            df, err = load_and_process(uploaded_file.read(), uploaded_file.name)
        if err:
            st.error(f"❌ Error: {err}")
            return
        st.success(f"✅ Data loaded: {len(df)} records")
    else:
        st.warning("👈 Please upload a fitness data file or enable the demo dataset in the sidebar.")
        st.markdown("""
        **Expected columns:**
        - `timestamp` — datetime (e.g., 2024-01-01 08:00:00)
        - `heart_rate_bpm` — heart rate in BPM
        - `steps` — step count per interval
        - `spo2_pct` — blood oxygen %
        - `sleeping` — 0/1 flag (optional)
        """)
        return

    # ── Date Filter ──
    date_range = st.date_input(
        "Select date range",
        value=(df.index.min().date(), df.index.max().date()),
        min_value=df.index.min().date(),
        max_value=df.index.max().date(),
    )
    if len(date_range) == 2:
        df = df[(df.index.date >= date_range[0]) & (df.index.date <= date_range[1])]

    if df.empty:
        st.warning("No data for selected range.")
        return

    # ── KPI Cards ──
    total = len(df)
    n_anom = int(df["final_anomaly"].sum())
    n_high = int((df["severity"] == "high").sum())

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Total Records",    f"{total:,}")
    col2.metric("⚠️ Anomalies",        f"{n_anom:,}", f"{n_anom/total*100:.1f}%")
    col3.metric("🔴 High Severity",    f"{n_high:,}")
    col4.metric("💓 Avg HR",           f"{df['heart_rate_bpm'].mean():.0f} bpm")
    col5.metric("🩸 Avg SpO2",         f"{df['spo2_pct'].mean():.1f}%")

    st.divider()

    # ── Metric Selector ──
    selected_metric = st.selectbox(
        "🔍 Select metric to visualize",
        ["Heart Rate", "Steps", "SpO2", "All metrics"],
    )

    if selected_metric in ("Heart Rate", "All metrics"):
        st.plotly_chart(
            plot_metric(df, "heart_rate_bpm", "Heart Rate (bpm)", "#E74C3C",
                        threshold_high=hr_high, threshold_low=hr_low),
            use_container_width=True
        )

    if selected_metric in ("Steps", "All metrics"):
        st.plotly_chart(
            plot_metric(df, "steps", "Steps (per 5 min)", "#2ECC71"),
            use_container_width=True
        )

    if selected_metric in ("SpO2", "All metrics"):
        st.plotly_chart(
            plot_metric(df, "spo2_pct", "SpO2 (%)", "#3498DB",
                        threshold_low=spo2_low),
            use_container_width=True
        )

    # ── Analytics Row ──
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_daily_anomaly_rate(df), use_container_width=True)
    with c2:
        pie_fig = plot_anomaly_type_pie(df)
        if pie_fig:
            st.plotly_chart(pie_fig, use_container_width=True)

    # ── Anomaly Table ──
    st.subheader("🚨 Anomaly Log")
    anomaly_df = df[df["final_anomaly"] == 1][
        ["heart_rate_bpm", "steps", "spo2_pct", "severity", "anomaly_score"]
    ].sort_values("anomaly_score", ascending=False)

    if not anomaly_df.empty:
        st.dataframe(
            anomaly_df.style.background_gradient(subset=["anomaly_score"], cmap="Reds"),
            height=300, use_container_width=True
        )
    else:
        st.success("✅ No anomalies detected in selected range!")

    # ── Export ──
    st.subheader("📥 Export Reports")
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            "⬇️ Download Anomaly CSV",
            data=generate_csv_report(df),
            file_name="fitpulse_anomalies.csv",
            mime="text/csv",
        )
    with ec2:
        st.download_button(
            "⬇️ Download Summary Report (TXT)",
            data=generate_summary_report(df),
            file_name="fitpulse_summary_report.txt",
            mime="text/plain",
        )


if __name__ == "__main__":
    main()
