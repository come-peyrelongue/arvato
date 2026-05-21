import streamlit as st
import pandas as pd

from utils import *
from translations import t

lang = st.session_state.get("lang", "fr")

st.title(t("Tableau de bord", lang))

companies = load_companies()

# ============================================================
# REAL STATS
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
    st.metric(t("Entreprises enregistrées", lang), company_count)

with col2:
    st.metric(t("Simulations de prévision", lang), simulation_count)

with col3:
    st.metric(t("Feedbacks soumis", lang), feedback_count)

st.markdown("---")

# ============================================================
# FEEDBACK COEFFICIENT EVOLUTION
# ============================================================

st.subheader(t("Evolution du coefficient de feedback", lang))

if not fb_df.empty and "submitted_at" in fb_df.columns and "counts" in fb_df.columns:

    fb_df["submitted_at"] = pd.to_datetime(fb_df["submitted_at"], errors="coerce")
    fb_df = fb_df.dropna(subset=["submitted_at"])
    fb_df = fb_df.sort_values("submitted_at")

    counted = fb_df[fb_df["counts"] == True].copy()

    if not counted.empty:
        counted["is_positive"] = (counted["status"] == "OK").astype(int)
        counted["cumulative_positive"] = counted["is_positive"].cumsum()
        counted["cumulative_total"] = range(1, len(counted) + 1)
        counted["rolling_coefficient"] = counted["cumulative_positive"] / counted["cumulative_total"]

        st.line_chart(
            counted.set_index("submitted_at")["rolling_coefficient"],
            use_container_width=True
        )

        st.caption(t("Coefficient de feedback glissant (ratio des résultats positifs sur le total des feedbacks comptabilisés)", lang))
    else:
        st.info(t("Aucun feedback comptabilisé. Soumettez des feedbacks avec des simulations actives pour voir l'évolution.", lang))
else:
    st.info(t("Aucune donnée de feedback disponible.", lang))

st.markdown("---")

# ============================================================
# AI CONFIDENCE TREND
# ============================================================

st.subheader(t("Tendance de confiance IA", lang))

if not sim_df.empty and "confidence" in sim_df.columns and "created_at" in sim_df.columns:

    sim_df["created_at"] = pd.to_datetime(sim_df["created_at"], errors="coerce")
    sim_df = sim_df.dropna(subset=["created_at"])
    sim_df = sim_df.sort_values("created_at")

    sim_df["rolling_confidence"] = sim_df["confidence"].rolling(window=5, min_periods=1).mean()

    col_chart, col_stats = st.columns([3, 1])

    with col_chart:
        st.line_chart(
            sim_df.set_index("created_at")[["confidence", "rolling_confidence"]],
            use_container_width=True
        )
        st.caption(t("Confiance par simulation et moyenne glissante sur 5", lang))

    with col_stats:
        avg_conf = sim_df["confidence"].mean()
        last_conf = sim_df["confidence"].iloc[-1] if len(sim_df) > 0 else 0

        st.metric(t("Confiance moyenne", lang), f"{avg_conf:.2f}")
        st.metric(t("Derniere simulation", lang), f"{last_conf:.2f}")

        if len(sim_df) >= 5:
            first_5 = sim_df["confidence"].head(5).mean()
            last_5 = sim_df["confidence"].tail(5).mean()
            delta = last_5 - first_5
            st.metric(t("Tendance (5 derniers vs 5 premiers)", lang), f"{delta:+.2f}")

else:
    st.info(t("Aucune donnée de simulation disponible.", lang))

st.markdown("---")

# ============================================================
# SIMULATION BREAKDOWN
# ============================================================

st.subheader(t("Répartition des simulations", lang))

if not sim_df.empty and "pole" in sim_df.columns:

    col_pole, col_company = st.columns(2)

    with col_pole:
        st.write(f"**{t('Par pôle', lang)}**")
        pole_counts = sim_df["pole"].value_counts()
        st.bar_chart(pole_counts, use_container_width=True)

    with col_company:
        if "company" in sim_df.columns:
            st.write(f"**{t('Par entreprise', lang)}**")
            company_counts = sim_df["company"].value_counts()
            st.bar_chart(company_counts, use_container_width=True)

else:
    st.info(t("Lancez des simulations pour voir la répartition.", lang))