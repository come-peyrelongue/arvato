import streamlit as st
import pandas as pd

from utils import *

st.title("Dashboard")

companies = load_companies()

# ============================================================
# REAL STATS
# ============================================================

company_count = len(companies)

simulation_count = 0

if SIMULATION_FILE.exists():

    sim_df = pd.read_csv(SIMULATION_FILE)

    simulation_count = len(sim_df)

# ============================================================
# UI
# ============================================================

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Registered Companies",
        company_count
    )

with col2:

    st.metric(
        "Forecast Simulations",
        simulation_count
    )
