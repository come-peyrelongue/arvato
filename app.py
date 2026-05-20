import streamlit as st

st.set_page_config(
    page_title="Staffing Forecast System",
    layout="wide"
)

pages = {
    "Dashboard": [
        st.Page("dashboard.py", title="Dashboard", icon=":material/home:"),
    ],

    "Management": [
        st.Page("companies.py", title="Companies", icon=":material/enterprise:"),
        st.Page("productivity.py", title="Productivity", icon=":material/avg_pace:"),
    ],

    "Operations": [
        st.Page("ingestion.py", title="Data Ingestion", icon=":material/data_check:"),
        st.Page("forecast.py", title="Forecast", icon=":material/readiness_score:"),
        st.Page("feedback.py", title="Feedback", icon=":material/add_reaction:"),
    ],
}

pg = st.navigation(pages)

pg.run()