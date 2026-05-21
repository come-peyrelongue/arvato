import streamlit as st

st.set_page_config(
    page_title="Staffing Forecast System",
    layout="wide",
    page_icon="img/favicon.png",
)

# =========================
# LOGO (tout en haut de la sidebar, au-dessus de la navigation)
# =========================

st.logo("img/logo.png", size="large", icon_image="img/favicon.png")

# =========================
# CSS OPTIMIZATIONS
# =========================

st.markdown("""
<style>
@font-face {
    font-display: swap !important;
}
[data-testid="stMetric"] {
    min-height: 80px;
}
[data-testid="stVegaLiteChart"],
.stLineChart,
.stBarChart {
    min-height: 300px;
}
[data-testid="stSidebar"] {
    min-width: 250px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LANGUAGE SELECTOR
# =========================

LANGUAGES = {
    "Francais": "fr",
    "English": "en",
    "Espanol": "es",
    "Deutsch": "de",
    "Italiano": "it",
    "Portugues": "pt",
    "Nederlands": "nl",
    "Polski": "pl",
    "Romana": "ro",
    "Turkce": "tr",
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja",
    "Korean": "ko",
    "Russian": "ru",
}

if "lang" not in st.session_state:
    st.session_state.lang = "fr"

lang_names = list(LANGUAGES.keys())
lang_codes = list(LANGUAGES.values())
current_index = lang_codes.index(st.session_state.lang) if st.session_state.lang in lang_codes else 0

selected_lang_name = st.sidebar.selectbox(
    "Langue / Language",
    options=lang_names,
    index=current_index
)

st.session_state.lang = LANGUAGES[selected_lang_name]

# =========================
# TRANSLATION
# =========================

from translations import t

lang = st.session_state.lang

# =========================
# PAGES
# =========================

pages = {
    t("Tableau de bord", lang): [
        st.Page("dashboard.py", title=t("Tableau de bord", lang), icon=":material/home:"),
    ],

    t("Gestion", lang): [
        st.Page("companies.py", title=t("Entreprises", lang), icon=":material/enterprise:"),
        st.Page("productivity.py", title=t("Productivité", lang), icon=":material/avg_pace:"),
    ],

    t("Opérations", lang): [
        st.Page("ingestion.py", title=t("Ingestion des données", lang), icon=":material/data_check:"),
        st.Page("forecast.py", title=t("Prévision", lang), icon=":material/readiness_score:"),
        st.Page("feedback.py", title=t("Feedback", lang), icon=":material/add_reaction:"),
    ],
}

pg = st.navigation(pages)

pg.run()