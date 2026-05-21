import streamlit as st

from utils import *
from translations import t

lang = st.session_state.get("lang", "fr")

st.title(t("Productivité", lang))

companies = load_companies()

company = st.selectbox(t("Entreprise", lang), companies)

prod = load_productivity(company)

new_prod = {}

cols = st.columns(4)

for i, pole in enumerate(POLES):

    with cols[i]:

        new_prod[pole] = st.number_input(
            pole,
            value=float(
                prod.get(
                    pole,
                    DEFAULT_PRODUCTIVITY[pole]
                )
            )
        )

if st.button(t("Enregistrer la productivite", lang), use_container_width=True):

    save_productivity(company, new_prod)

    st.success(t("Enregistre", lang))