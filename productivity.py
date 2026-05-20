import streamlit as st

from utils import *

st.title("Productivity")

companies = load_companies()

company = st.selectbox("Company", companies)

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

if st.button("Save Productivity"):

    save_productivity(company, new_prod)

    st.success("Saved")