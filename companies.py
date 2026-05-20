import streamlit as st
from utils import *

st.title("Company Management")

# CSS to vertically align elements within columns
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

st.subheader("Create company")

new_company = st.text_input("Company name")

if st.button("Create company", use_container_width=True):
    if new_company:
        if new_company not in companies:
            companies.append(new_company)
            save_companies(companies)
            st.success("Company created")
            st.rerun()
        else:
            st.warning("Company already exists")

# ============================================================
# LIST
# ============================================================

st.markdown("---")

st.subheader("Existing companies")

if not companies:
    st.info("No companies registered")
else:
    # Headers
    header_cols = st.columns([3, 4, 2, 2])
    header_cols[0].markdown("")
    header_cols[1].markdown("")
    header_cols[2].markdown("")
    header_cols[3].markdown("")

    st.markdown("---")

    for company in companies:

        col_name, col_input, col_rename, col_delete = st.columns([3, 4, 2, 2])

        # NAME
        col_name.write(company)

        # RENAME INPUT
        new_name = col_input.text_input(
            "New name",
            key=f"rename_{company}",
            label_visibility="collapsed",
            placeholder="New name…",
        )

        # RENAME BUTTON
        if col_rename.button(
            "Rename",
            key=f"rename_btn_{company}",
            use_container_width=True,
        ):
            if new_name:
                companies = [
                    new_name if c == company else c for c in companies
                ]
                save_companies(companies)
                st.success("Company renamed")
                st.rerun()

        # DELETE BUTTON
        if col_delete.button(
            "Delete",
            key=f"delete_{company}",
            use_container_width=True,
        ):
            companies.remove(company)
            save_companies(companies)
            st.success("Company deleted")
            st.rerun()

        st.markdown("---")