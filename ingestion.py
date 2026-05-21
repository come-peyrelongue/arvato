import streamlit as st
import pandas as pd

from utils import *
from translations import t

lang = st.session_state.get("lang", "fr")

st.title(t("Ingestion des donnees", lang))

# ============================================================
# TABS
# ============================================================

tab_real, tab_forecast = st.tabs([t("Donnees reelles", lang), t("Donnees previsionnelles", lang)])

# ============================================================
# REAL DATA
# ============================================================

with tab_real:

    st.subheader(t("Fichiers reels importes", lang))

    files = list(REAL_DATA_DIR.glob("*"))

    if len(files) == 0:
        st.info(t("Aucune donnee reelle importee.", lang))
    else:
        st.write([f.name for f in files])

    uploaded_real = st.file_uploader(
        t("Importer un fichier Excel de donnees reelles", lang),
        type=["xlsx"],
        key="real_upload"
    )

    if uploaded_real:

        st.dataframe(pd.read_excel(uploaded_real).head())

        if st.button(t("Traiter les donnees reelles", lang), key="btn_real"):

            df = pd.read_excel(uploaded_real)

            split_and_store(df, mode="real")

            REAL_DATA_DIR.joinpath(
                uploaded_real.name
            ).write_bytes(uploaded_real.getbuffer())

            st.success(t("Donnees reelles importees avec succes", lang))


# ============================================================
# FORECAST DATA
# ============================================================

with tab_forecast:

    st.subheader(t("Ingestion des previsions", lang))

    forecast_file = FORECAST_DATA_DIR / "forecast_history.csv"

    if forecast_file.exists():
        st.write(t("Historique de previsions charge", lang))
        st.dataframe(pd.read_csv(forecast_file).head())
    else:
        st.info(t("Aucune donnee previsionnelle.", lang))

    uploaded_forecast = st.file_uploader(
        t("Importer un fichier Excel de previsions", lang),
        type=["xlsx"],
        key="forecast_upload"
    )

    if uploaded_forecast:

        df = pd.read_excel(uploaded_forecast)
        st.dataframe(df.head())

        if st.button(t("Enregistrer les previsions", lang), key="btn_forecast"):

            df["upload_date"] = pd.Timestamp.today()

            if forecast_file.exists():
                old = pd.read_csv(forecast_file)
                df = pd.concat([old, df], ignore_index=True)

            df.to_csv(forecast_file, index=False)

            st.success(t("Previsions enregistrees avec succes", lang))