import streamlit as st
import pandas as pd

from utils import (
    load_companies,
    get_simulation_for_date,
    update_feedback,
    normalize_company,
    FEEDBACK_FILE,
    DATA_DIR
)

st.title("Feedback")

companies = load_companies()

if not companies:
    st.error("No companies registered")
    st.stop()

# =========================
# INPUTS
# =========================

col1, col2 = st.columns(2)

with col1:
    company = st.selectbox("Company", companies)

with col2:
    date = st.date_input("Week start date")

# =========================
# CHECK IF FEEDBACK ALREADY EXISTS
# =========================

feedback_already_given = False
existing_feedback_index = None

if FEEDBACK_FILE.exists():
    fb_df = pd.read_csv(FEEDBACK_FILE)
    if not fb_df.empty:
        mask = (
            (fb_df["company"] == normalize_company(company)) &
            (fb_df["date"] == str(date))
        )
        if mask.any():
            feedback_already_given = True
            existing_feedback_index = fb_df[mask].index.tolist()

# =========================
# SHOW SIMULATION IF EXISTS
# =========================

st.markdown("---")

simulations = get_simulation_for_date(company, date)

if simulations:
    st.subheader("Simulation found for this week")

    for sim in simulations:
        with st.container():
            cols = st.columns([2, 2, 2, 2, 3])
            cols[0].metric("Pole", sim["pole"])
            cols[1].metric("Employees recommended", sim["employees_recommended"])
            cols[2].metric("AI Coefficient", f"{sim['ai_coef']:.2f}")
            cols[3].metric("Confidence", f"{sim['confidence']:.2f}")
            created_dt = pd.to_datetime(sim["created_at"])
            cols[4].metric("Created at", created_dt.strftime("%Y/%m/%d %H:%M"))
        st.markdown("---")

    simulation_exists = True
else:
    st.info("No simulation found for this date and company.")
    simulation_exists = False

# =========================
# BLOCK IF ALREADY SUBMITTED
# =========================

if feedback_already_given:
    st.warning(f"A feedback has already been submitted for {company} on {date}.")

    with st.expander("Manage feedbacks"):

        fb_df = pd.read_csv(FEEDBACK_FILE)
        mask = (
            (fb_df["company"] == normalize_company(company)) &
            (fb_df["date"] == str(date))
        )
        existing = fb_df[mask]

        for idx, row in existing.iterrows():
            col_info, col_delete = st.columns([4, 1])

            with col_info:
                submitted = pd.to_datetime(row.get("submitted_at", ""), errors="coerce")
                submitted_str = submitted.strftime("%Y/%m/%d %H:%M") if pd.notna(submitted) else "N/A"
                status_display = row.get("status", "N/A")
                counted = "Yes" if row.get("counts") else "No"
                real_staff = row.get("real_staff", "N/A")

                st.markdown(
                    f"**Status:** {status_display} | "
                    f"**Counts:** {counted} | "
                    f"**Real staff:** {real_staff} | "
                    f"**Submitted:** {submitted_str}"
                )

            with col_delete:
                if st.button("Delete", key=f"delete_fb_{idx}", use_container_width=True):
                    fb_df = fb_df.drop(idx)
                    fb_df.to_csv(FEEDBACK_FILE, index=False)
                    st.success("Feedback deleted.")
                    st.rerun()

    st.stop()

# =========================
# FEEDBACK FORM
# =========================

st.subheader("Submit Feedback")

status = st.selectbox(
    "How did the week go?",
    [
        "OK — Week went well",
        "KO_EXTERNE — Problem due to external event",
        "KO_SUIVI — Problem, but team followed the recommendation",
        "KO_NON_SUIVI — Problem, team did NOT follow the recommendation"
    ]
)

# Extract status key
status_key = status.split(" — ")[0]

# =========================
# DETERMINE IF FEEDBACK COUNTS
# =========================

counts = False
reason_no_count = ""

if status_key == "OK":
    if simulation_exists:
        counts = True
    else:
        reason_no_count = "Week was OK but no simulation existed — nothing to validate."

elif status_key == "KO_EXTERNE":
    reason_no_count = "External event — not representative, feedback won't affect coefficients."

elif status_key == "KO_SUIVI":
    if simulation_exists:
        counts = True
    else:
        reason_no_count = "No simulation existed for this date."

elif status_key == "KO_NON_SUIVI":
    reason_no_count = "Team did not follow the recommendation — cannot evaluate the model."

# =========================
# DISPLAY IMPACT PREVIEW
# =========================

if counts:
    if status_key == "OK":
        st.success("This feedback will positively impact the model (recommendation was correct).")
    elif status_key == "KO_SUIVI":
        st.warning("This feedback will negatively impact the model (recommendation was followed but insufficient).")
else:
    st.info(f"This feedback will NOT affect coefficients. Reason: {reason_no_count}")

# =========================
# OPTIONAL: REAL STAFF USED
# =========================

real_staff = None
if status_key == "KO_SUIVI":
    real_staff = st.number_input(
        "How many employees were actually needed?",
        min_value=0,
        value=0
    )

# =========================
# SUBMIT
# =========================

if st.button("Submit Feedback", use_container_width=True):

    row = {
        "company": normalize_company(company),
        "date": str(date),
        "status": status_key,
        "simulation_existed": simulation_exists,
        "counts": counts,
        "real_staff": real_staff,
        "submitted_at": pd.Timestamp.now().isoformat()
    }

    if FEEDBACK_FILE.exists():
        old = pd.read_csv(FEEDBACK_FILE)
        df = pd.concat([old, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(FEEDBACK_FILE, index=False)

    update_feedback(company, status_key, counts)

    if counts:
        st.success("Feedback saved and coefficients updated.")
    else:
        st.success("Feedback saved (coefficients unchanged).")

    st.rerun()