import streamlit as st

from utils import *

st.title("Company Management")

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

    for company in companies:

        col1, col2, col3 = st.columns([5, 3, 2])

        with col1:
            st.write(f"### {company}")

        # ====================================================
        # RENAME
        # ====================================================

        with col2:

            new_name = st.text_input(
                f"Rename {company}",
                key=f"rename_{company}"
            )

            if st.button(
                "Rename",
                key=f"rename_btn_{company}"
            ):

                if new_name:

                    companies = [
                        new_name if c == company else c
                        for c in companies
                    ]

                    save_companies(companies)

                    st.success("Company renamed")

                    st.rerun()

        # ====================================================
        # DELETE
        # ====================================================

        with col3:

            if st.button(
                "Delete",
                key=f"delete_{company}",
                use_container_width=True
            ):

                companies.remove(company)

                save_companies(companies)

                st.success("Company deleted")

                st.rerun()