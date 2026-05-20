import streamlit as st
import pandas as pd
from utils import *

st.title("Data Ingestion")

# ============================================================
# TABS (REAL / FORECAST)
# ============================================================

tab_real, tab_forecast = st.tabs(["📦 Real Data", "📈 Forecast Data"])

# ============================================================
# REAL DATA
# ============================================================

with tab_real:

    st.subheader("Imported real files")

    files = list(REAL_DATA_DIR.glob("*"))

    if len(files) == 0:
        st.info("No real data uploaded yet.")
    else:
        st.write([f.name for f in files])

    uploaded_real = st.file_uploader(
        "Upload Real Data Excel",
        type=["xlsx"],
        key="real_upload"
    )

    if uploaded_real:

        st.dataframe(pd.read_excel(uploaded_real).head())

        if st.button("Process Real Data", key="btn_real"):

            df = pd.read_excel(uploaded_real)

            split_and_store(df, mode="real")

            REAL_DATA_DIR.joinpath(
                uploaded_real.name
            ).write_bytes(uploaded_real.getbuffer())

            st.success("Real data imported successfully")


# ============================================================
# FORECAST DATA
# ============================================================

with tab_forecast:

    st.subheader("Forecast ingestion")

    forecast_file = FORECAST_DATA_DIR / "forecast_history.csv"

    if forecast_file.exists():
        st.write("Existing forecast history loaded")
        st.dataframe(pd.read_csv(forecast_file).head())
    else:
        st.info("No forecast data yet.")

    uploaded_forecast = st.file_uploader(
        "Upload Forecast Excel",
        type=["xlsx"],
        key="forecast_upload"
    )

    if uploaded_forecast:

        df = pd.read_excel(uploaded_forecast)
        st.dataframe(df.head())

        if st.button("Store Forecast", key="btn_forecast"):

            df["upload_date"] = pd.Timestamp.today()

            if forecast_file.exists():
                old = pd.read_csv(forecast_file)
                df = pd.concat([old, df], ignore_index=True)

            df.to_csv(forecast_file, index=False)

            st.success("Forecast stored successfully")