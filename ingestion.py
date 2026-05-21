import streamlit as st
import pandas as pd

from utils import *
from translations import t

lang = st.session_state.get("lang", "fr")

st.title(t("Ingestion des données", lang))

# ============================================================
# TABS
# ============================================================

tab_real, tab_forecast = st.tabs([t("Données réelles", lang), t("Données prévisionnelles", lang)])

# ============================================================
# REAL DATA
# ============================================================

with tab_real:

    st.subheader(t("Fichiers réels importés", lang))

    files = list(REAL_DATA_DIR.glob("*"))

    if len(files) == 0:
        st.info(t("Aucune donnée réelle importée.", lang))
    else:
        st.write([f.name for f in files])

    uploaded_real = st.file_uploader(
        t("Importer un fichier Excel de donnees réelles", lang),
        type=["xlsx"],
        key="real_upload"
    )

    if uploaded_real:

        st.dataframe(pd.read_excel(uploaded_real).head())

        if st.button(t("Traiter les donnees réelles", lang), key="btn_real"):

            df = pd.read_excel(uploaded_real)

            split_and_store(df, mode="real")

            REAL_DATA_DIR.joinpath(
                uploaded_real.name
            ).write_bytes(uploaded_real.getbuffer())

            st.success(t("Données réelles importées avec succès", lang))


# ============================================================
# FORECAST DATA
# ============================================================

with tab_forecast:

    st.subheader(t("Ingestion des prévisions", lang))

    forecast_file = FORECAST_DATA_DIR / "forecast_history.csv"

    if forecast_file.exists():
        st.write(t("Historique de prévisions chargé", lang))
        st.dataframe(pd.read_csv(forecast_file).head())
    else:
        st.info(t("Aucune donnée previsionnelle.", lang))

    uploaded_forecast = st.file_uploader(
        t("Importer un fichier Excel de prévisions", lang),
        type=["xlsx"],
        key="forecast_upload"
    )

    if uploaded_forecast:

        df = pd.read_excel(uploaded_forecast)
        st.dataframe(df.head())

        if st.button(t("Enregistrer les prévisions", lang), key="btn_forecast"):

            df["upload_date"] = pd.Timestamp.today()

            if forecast_file.exists():
                old = pd.read_csv(forecast_file)
                df = pd.concat([old, df], ignore_index=True)

            df.to_csv(forecast_file, index=False)

            st.success(t("Prévisions enregistrées avec succès", lang))