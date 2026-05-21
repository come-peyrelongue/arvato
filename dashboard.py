import streamlit as st
import pandas as pd

from utils import *

st.title("Dashboard")

companies = load_companies()

# ============================================================
# METRICS
# ============================================================

company_count = len(companies)

simulation_count = 0
sim_df = pd.DataFrame()

if SIMULATION_FILE.exists():
    sim_df = pd.read_csv(SIMULATION_FILE)
    simulation_count = len(sim_df)

feedback_count = 0
fb_df = pd.DataFrame()

if FEEDBACK_FILE.exists():
    fb_df = pd.read_csv(FEEDBACK_FILE)
    feedback_count = len(fb_df)

# ============================================================
# TOP METRICS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Registered Companies", company_count)

with col2:
    st.metric("Forecast Simulations", simulation_count)

with col3:
    st.metric("Feedbacks Submitted", feedback_count)

st.markdown("---")

# ============================================================
# FEEDBACK COEFFICIENT EVOLUTION
# ============================================================

st.subheader("Feedback Coefficient Evolution")

if not fb_df.empty and "submitted_at" in fb_df.columns and "counts" in fb_df.columns:

    fb_df["submitted_at"] = pd.to_datetime(fb_df["submitted_at"], errors="coerce")
    fb_df = fb_df.dropna(subset=["submitted_at"])
    fb_df = fb_df.sort_values("submitted_at")

    # Only feedbacks that count
    counted = fb_df[fb_df["counts"] == True].copy()

    if not counted.empty:
        # Compute running positive ratio
        counted["is_positive"] = (counted["status"] == "OK").astype(int)
        counted["cumulative_positive"] = counted["is_positive"].cumsum()
        counted["cumulative_total"] = range(1, len(counted) + 1)
        counted["rolling_coefficient"] = counted["cumulative_positive"] / counted["cumulative_total"]
        counted["date_label"] = counted["submitted_at"].dt.strftime("%Y/%m/%d")

        st.line_chart(
            counted.set_index("submitted_at")["rolling_coefficient"],
            use_container_width=True
        )

        st.caption("Rolling feedback coefficient (ratio of positive outcomes over total counted feedbacks)")
    else:
        st.info("No counted feedbacks yet. Submit feedbacks with active simulations to see evolution.")
else:
    st.info("No feedback data available yet.")

st.markdown("---")

# ============================================================
# AI CONFIDENCE TREND (creative addition)
# ============================================================

st.subheader("AI Confidence Trend")

if not sim_df.empty and "confidence" in sim_df.columns and "created_at" in sim_df.columns:

    sim_df["created_at"] = pd.to_datetime(sim_df["created_at"], errors="coerce")
    sim_df = sim_df.dropna(subset=["created_at"])
    sim_df = sim_df.sort_values("created_at")

    # Rolling average confidence (window of 5 simulations)
    sim_df["rolling_confidence"] = sim_df["confidence"].rolling(window=5, min_periods=1).mean()

    col_chart, col_stats = st.columns([3, 1])

    with col_chart:
        st.line_chart(
            sim_df.set_index("created_at")[["confidence", "rolling_confidence"]],
            use_container_width=True
        )
        st.caption("Per-simulation confidence and 5-simulation rolling average")

    with col_stats:
        avg_conf = sim_df["confidence"].mean()
        last_conf = sim_df["confidence"].iloc[-1] if len(sim_df) > 0 else 0

        st.metric("Average Confidence", f"{avg_conf:.2f}")
        st.metric("Last Simulation", f"{last_conf:.2f}")

        # Trend indicator
        if len(sim_df) >= 5:
            first_5 = sim_df["confidence"].head(5).mean()
            last_5 = sim_df["confidence"].tail(5).mean()
            delta = last_5 - first_5
            st.metric("Trend (last 5 vs first 5)", f"{delta:+.2f}")

else:
    st.info("No simulation data available yet.")

st.markdown("---")

# ============================================================
# POLE DISTRIBUTION & COMPANY ACTIVITY (creative)
# ============================================================

st.subheader("Simulation Breakdown")

if not sim_df.empty and "pole" in sim_df.columns:

    col_pole, col_company = st.columns(2)

    with col_pole:
        st.write("**By Pole**")
        pole_counts = sim_df["pole"].value_counts()
        st.bar_chart(pole_counts, use_container_width=True)

    with col_company:
        if "company" in sim_df.columns:
            st.write("**By Company**")
            company_counts = sim_df["company"].value_counts()
            st.bar_chart(company_counts, use_container_width=True)

else:
    st.info("Run some simulations to see the breakdown.")