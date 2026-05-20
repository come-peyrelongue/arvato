import streamlit as st
import pandas as pd
from datetime import timedelta
from pathlib import Path
import json
from math import ceil

# ============================================================
# CONFIG
# ============================================================

DATA_DIR = Path("data")
COMPANIES_FILE = DATA_DIR / "companies.json"
SIMULATION_FILE = DATA_DIR / "simulations.csv"

SHIFT_HOURS = 7

POLES = ["PICKING", "PROMO", "BULK", "GLOBAL"]

DEFAULT_PRODUCTIVITY = {
    "PICKING": 157,
    "PROMO": 125,
    "BULK": 100,
    "GLOBAL": 150
}

# ============================================================
# STORAGE HELPERS
# ============================================================

def load_companies():
    if not COMPANIES_FILE.exists():
        return []
    return json.loads(COMPANIES_FILE.read_text())


def productivity_file(company):
    return DATA_DIR / f"productivity_{company}.json"


def load_productivity(company):

    path = productivity_file(company)

    if not path.exists():
        return DEFAULT_PRODUCTIVITY

    return json.loads(path.read_text())


def coefficients_file():
    return DATA_DIR / "coefficients.json"


def load_coefficients():

    file = coefficients_file()

    if not file.exists():
        return {}

    return json.loads(file.read_text())


def get_feedback_coefficient(company):

    data = load_coefficients()

    if company not in data:
        return 1.0

    return data[company].get("feedback", 1.0)


def compute_historical_coefficient():

    forecast_file = DATA_DIR / "forecast" / "forecast_history.csv"

    if not forecast_file.exists():
        return 1.0

    df = pd.read_csv(forecast_file)

    if "forecast_lines" not in df.columns:
        return 1.0

    if "real_lines" not in df.columns:
        return 1.0

    total_forecast = df["forecast_lines"].sum()

    if total_forecast == 0:
        return 1.0

    return df["real_lines"].sum() / total_forecast


# ============================================================
# CALCULATION
# ============================================================

def compute_employees(lines, productivity, feedback_coef):

    capacity = productivity * SHIFT_HOURS * feedback_coef

    return ceil(lines / capacity)


def simulate_week(company, pole, start_date, total_lines):

    productivity = load_productivity(company).get(pole, 120)

    historical_coef = compute_historical_coefficient()

    feedback_coef = get_feedback_coefficient(company)

    adjusted_lines = (total_lines * historical_coef) / 4

    results = []

    for i in range(7):

        current_day = start_date + timedelta(days=i)

        employees = compute_employees(
            adjusted_lines,
            productivity,
            feedback_coef
        )

        results.append({
            "date": current_day.date(),
            "pole": pole,
            "forecast_lines": round(adjusted_lines),
            "employees_required": employees
        })

    return (
        pd.DataFrame(results),
        productivity,
        historical_coef,
        feedback_coef
    )


# ============================================================
# SAVE SIMULATION
# ============================================================

def save_simulation(company, df):

    df["company"] = company

    if SIMULATION_FILE.exists():

        old = pd.read_csv(SIMULATION_FILE)

        final = pd.concat([old, df], ignore_index=True)

    else:
        final = df

    final.to_csv(SIMULATION_FILE, index=False)


# ============================================================
# PAGE
# ============================================================

st.title("Forecast")

companies = load_companies()

if not companies:

    st.warning("No companies available.")

    st.stop()

# ============================================================
# HEADER
# ============================================================

col1, col2 = st.columns(2)

with col1:

    company = st.selectbox(
        "Company",
        companies
    )

with col2:

    pole = st.selectbox(
        "Pole",
        POLES
    )

# ============================================================
# INPUTS
# ============================================================

col3, col4 = st.columns(2)

with col3:

    start_date = st.date_input(
        "Start week"
    )

with col4:

    total_lines = st.number_input(
        "Monthly forecast lines",
        min_value=0,
        value=100000
    )

# ============================================================
# GENERATE BUTTON
# ============================================================

if st.button("Generate Forecast", use_container_width=True):

    (
        df,
        productivity,
        historical_coef,
        feedback_coef
    ) = simulate_week(
        company,
        pole,
        pd.to_datetime(start_date),
        total_lines
    )

    save_simulation(company, df)

    # ========================================================
    # EXPLANATION
    # ========================================================

    st.subheader("Calculation Explanation")

    st.markdown(f"""
    ### Forecast logic

    - Productivity: **{productivity} lines/hour**
    - Shift duration: **{SHIFT_HOURS} hours**
    - Historical coefficient: **{historical_coef:.2f}**
    - Feedback coefficient: **{feedback_coef:.2f}**

    ### Final formula

    Adjusted lines:

    ```text
    adjusted_lines = monthly_lines × historical_coefficient / 4
    ```

    Employee capacity:

    ```text
    capacity = productivity × shift_hours × feedback_coefficient
    ```

    Staffing calculation:

    ```text
    employees = adjusted_lines / capacity
    ```

    Final result is rounded up.
    """)

    # ========================================================
    # KPIS
    # ========================================================

    peak_staff = int(df["employees_required"].max())
    avg_staff = int(df["employees_required"].mean())

    k1, k2 = st.columns(2)

    with k1:
        st.metric(
            "Peak Staffing",
            peak_staff
        )

    with k2:
        st.metric(
            "Average Staffing",
            avg_staff
        )

    # ========================================================
    # TABLE
    # ========================================================

    st.subheader("Weekly Staffing Plan")

    st.dataframe(
        df,
        use_container_width=True
    )

    # ========================================================
    # CHART
    # ========================================================

    st.subheader("Employees Evolution")

    chart_df = df[["date", "employees_required"]]

    st.line_chart(
        chart_df.set_index("date")
    )