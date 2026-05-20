import streamlit as st
import pandas as pd

from utils import *

st.title("Feedback")

companies = load_companies()

company = st.selectbox("Company", companies)

date = st.date_input("Forecast Date")

status = st.selectbox(
    "Status",
    [
        "OK",
        "KO_EFFECTIF",
        "KO_EXTERNE"
    ]
)

real_staff = None

if status == "KO_EFFECTIF":

    real_staff = st.number_input(
        "Real Staff Used",
        min_value=0
    )

if st.button("Submit Feedback"):

    row = {
        "company": company,
        "date": str(date),
        "status": status,
        "real_staff": real_staff
    }

    if FEEDBACK_FILE.exists():

        old = pd.read_csv(FEEDBACK_FILE)

        df = pd.concat(
            [old, pd.DataFrame([row])],
            ignore_index=True
        )

    else:

        df = pd.DataFrame([row])

    df.to_csv(FEEDBACK_FILE, index=False)

    update_feedback(company, status)

    st.success("Feedback saved")