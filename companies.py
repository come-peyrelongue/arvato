import streamlit as st

from utils import *
from translations import t

lang = st.session_state.get("lang", "fr")

st.title(t("Gestion des entreprises", lang))

st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

companies = load_companies()

# ============================================================
# CREATE
# ============================================================

st.subheader(t("Créer une entreprise", lang))

new_company = st.text_input(t("Nom de l'entreprise", lang))

if st.button(t("Créer une entreprise", lang), use_container_width=True):

    if new_company:

        if new_company not in companies:

            companies.append(new_company)

            save_companies(companies)

            st.success(t("Entreprise créee", lang))

            st.rerun()

        else:
            st.warning(t("L'entreprise existe déjà", lang))

# ============================================================
# LIST
# ============================================================

st.markdown("---")

st.subheader(t("Entreprises existantes", lang))

if not companies:

    st.info(t("Aucune entreprise enregistrée", lang))

else:

    header_cols = st.columns([3, 4, 2, 2])
    header_cols[0].markdown(f"**{t('Entreprise', lang)}**")
    header_cols[1].markdown(f"**{t('Nouveau nom', lang)}**")
    header_cols[2].markdown("")
    header_cols[3].markdown("")

    st.markdown("---")

    for company in companies:

        col_name, col_input, col_rename, col_delete = st.columns([3, 4, 2, 2])

        col_name.write(company)

        new_name = col_input.text_input(
            t("Nouveau nom", lang),
            key=f"rename_{company}",
            label_visibility="collapsed",
            placeholder=t("Nouveau nom", lang) + "...",
        )

        if col_rename.button(
            t("Renommer", lang),
            key=f"rename_btn_{company}",
            use_container_width=True,
        ):
            if new_name:
                companies = [
                    new_name if c == company else c for c in companies
                ]
                save_companies(companies)
                st.success(t("Entreprise renommée", lang))
                st.rerun()

        if col_delete.button(
            t("Supprimer", lang),
            key=f"delete_{company}",
            use_container_width=True,
        ):
            companies.remove(company)
            save_companies(companies)
            st.success(t("Entreprise supprimée", lang))
            st.rerun()

        st.markdown("---")