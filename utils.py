import pandas as pd
import json
import re

from pathlib import Path
from math import ceil
from datetime import timedelta

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

REAL_DATA_DIR = DATA_DIR / "real"
FORECAST_DATA_DIR = DATA_DIR / "forecast"

REAL_DATA_DIR.mkdir(exist_ok=True)
FORECAST_DATA_DIR.mkdir(exist_ok=True)

SIMULATION_FILE = DATA_DIR / "simulations.csv"
COMPANIES_FILE = DATA_DIR / "companies.json"
COEF_FILE = DATA_DIR / "coefficients.json"
FEEDBACK_FILE = DATA_DIR / "feedback.csv"

SHIFT_HOURS = 7

POLES = ["PICKING", "PROMO", "BULK", "GLOBAL"]

DEFAULT_PRODUCTIVITY = {
    "PICKING": 157,
    "PROMO": 125,
    "BULK": 26.5,
    "GLOBAL": 27.6
}

# ============================================================
# COMPANIES
# ============================================================

def load_companies():

    if not COMPANIES_FILE.exists():
        return []

    return json.loads(COMPANIES_FILE.read_text())


def save_companies(companies):
    COMPANIES_FILE.write_text(json.dumps(companies, indent=4))

# ============================================================
# PRODUCTIVITY
# ============================================================

def productivity_file(company):
    return DATA_DIR / f"productivity_{company}.json"


def load_productivity(company):

    path = productivity_file(company)

    if not path.exists():
        path.write_text(json.dumps(DEFAULT_PRODUCTIVITY, indent=4))
        return DEFAULT_PRODUCTIVITY

    return json.loads(path.read_text())


def save_productivity(company, data):
    productivity_file(company).write_text(json.dumps(data, indent=4))

# ============================================================
# COEFFICIENTS
# ============================================================

def load_coefficients():

    if not COEF_FILE.exists():
        return {}

    return json.loads(COEF_FILE.read_text())


def save_coefficients(data):
    COEF_FILE.write_text(json.dumps(data, indent=4))


def get_company_coefficients(company):

    coef = load_coefficients().get(company, {})

    return {
        "feedback": coef.get("feedback", 1.0)
    }


def update_feedback(company, status):

    coef = load_coefficients()

    if company not in coef:
        coef[company] = {"feedback": 1.0}

    if status == "KO_EFFECTIF":
        coef[company]["feedback"] *= 0.97

    elif status == "OK":
        coef[company]["feedback"] *= 1.01

    save_coefficients(coef)

# ============================================================
# INGESTION
# ============================================================

def parse_workflow(workflow: str):

    match = re.match(
        r"PREPARATION_([A-Z])_([A-Z]+)(?:_(.+))?",
        workflow
    )

    if not match:
        return None, None, None

    return (
        match.group(1),
        match.group(2),
        match.group(3) or "GLOBAL"
    )


def split_and_store(df: pd.DataFrame, mode="real"):

    grouped = {}

    for _, row in df.iterrows():

        client, pole, country = parse_workflow(row["WORKFLOW"])

        if client is None:
            continue

        grouped.setdefault(client, []).append({
            "date": pd.to_datetime(row["DATE"]),
            "pole": pole,
            "quantity": int(row["QUANTITY"])
        })

    base_dir = REAL_DATA_DIR if mode == "real" else FORECAST_DATA_DIR

    for client, rows in grouped.items():

        file = base_dir / f"{client}.csv"

        new_df = pd.DataFrame(rows)

        if file.exists():
            old = pd.read_csv(file)
            final = pd.concat([old, new_df], ignore_index=True)
        else:
            final = new_df

        final.to_csv(file, index=False)

# ============================================================
# HISTORICAL COEF
# ============================================================

def compute_historical_coefficient():

    file = FORECAST_DATA_DIR / "forecast_history.csv"

    if not file.exists():
        return 1.0

    df = pd.read_csv(file)

    if "real_lines" not in df.columns:
        return 1.0

    if len(df) == 0:
        return 1.0

    return df["real_lines"].sum() / max(
        df["forecast_lines"].sum(),
        1
    )

# ============================================================
# FORECAST
# ============================================================

def compute_employees(lines, productivity, feedback_coef):

    capacity = productivity * SHIFT_HOURS * feedback_coef

    return ceil(lines / capacity)


def simulate_week(company, pole, start_date, total_lines):

    prod = load_productivity(company).get(pole, 120)

    hist_coef = compute_historical_coefficient()

    feedback_coef = get_company_coefficients(company)["feedback"]

    days = [
        start_date + timedelta(days=i)
        for i in range(7)
    ]

    adjusted_lines = (total_lines * hist_coef) / 4

    results = []

    for d in days:

        results.append({
            "date": d.date(),
            "pole": pole,
            "lines": round(adjusted_lines),
            "employees_required": compute_employees(
                adjusted_lines,
                prod,
                feedback_coef
            )
        })

    return (
        pd.DataFrame(results),
        prod,
        hist_coef,
        feedback_coef
    )

# ============================================================
# SIMULATION
# ============================================================

def save_simulation(company, pole, lines, employees):

    row = pd.DataFrame([{
        "company": company,
        "pole": pole,
        "lines": lines,
        "employees": employees,
        "date": pd.Timestamp.now()
    }])

    if SIMULATION_FILE.exists():

        old = pd.read_csv(SIMULATION_FILE)

        row = pd.concat([old, row], ignore_index=True)

    row.to_csv(SIMULATION_FILE, index=False)