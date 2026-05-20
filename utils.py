import pandas as pd
import json
import re
import os
from pathlib import Path
from math import ceil
from datetime import timedelta

# =========================
# BASE PATH (ROBUSTE STREAMLIT)
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

REAL_DATA_DIR = DATA_DIR / "real"
FORECAST_DATA_DIR = DATA_DIR / "forecast"

REAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
FORECAST_DATA_DIR.mkdir(parents=True, exist_ok=True)

COMPANIES_FILE = DATA_DIR / "companies.json"
SIMULATION_FILE = DATA_DIR / "simulations.csv"
COEF_FILE = DATA_DIR / "coefficients.json"

SHIFT_HOURS = 7
POLES = ["PICKING", "PROMO", "BULK", "GLOBAL"]

# =========================
# PRODUCTIVITY DEFAULT
# =========================
DEFAULT_PRODUCTIVITY = {
    "PICKING": 157,
    "PROMO": 125,
    "BULK": 26.5,
    "GLOBAL": 27.6
}

# =========================
# SAFE COMPANY NORMALIZATION
# =========================
def normalize_company(company: str) -> str:
    if not company:
        return ""
    return str(company).strip().upper()


def possible_company_files(company: str):
    c = normalize_company(company)
    return [
        REAL_DATA_DIR / f"{c}.csv",
        REAL_DATA_DIR / f"{c.lower()}.csv",
        REAL_DATA_DIR / f"{c.capitalize()}.csv",
    ]


# =========================
# COMPANIES
# =========================
def load_companies():
    if not COMPANIES_FILE.exists():
        return []
    return json.loads(COMPANIES_FILE.read_text())


# =========================
# PRODUCTIVITY
# =========================
def productivity_file(company):
    return DATA_DIR / f"productivity_{normalize_company(company)}.json"


def load_productivity(company):
    path = productivity_file(company)
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_PRODUCTIVITY, indent=2))
        return DEFAULT_PRODUCTIVITY
    return json.loads(path.read_text())


# =========================
# COEFFICIENTS
# =========================
def load_coefficients():
    if not COEF_FILE.exists():
        return {}
    return json.loads(COEF_FILE.read_text())


def get_feedback_coefficient(company):
    data = load_coefficients()
    return data.get(normalize_company(company), {}).get("feedback", 1.0)


# =========================
# HISTORICAL DATA (FIX CRITIQUE)
# =========================
def get_historical_data_for_ai(company):
    """
    IMPORTANT FIX:
    - cherche plusieurs variantes de fichier
    - évite le bug "fichier jamais trouvé"
    """
    company = normalize_company(company)

    file_candidates = [
        REAL_DATA_DIR / f"{company}.csv",
        REAL_DATA_DIR / f"{company.lower()}.csv",
    ]

    df = None
    for f in file_candidates:
        if f.exists():
            df = pd.read_csv(f)
            break

    if df is None or df.empty:
        return []

    if "date" not in df.columns:
        return []

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df["month"] = df["date"].dt.to_period("M").astype(str)

    grouped = df.groupby("month")["quantity"].sum().reset_index()

    history = [
        {
            "period": row["month"],
            "real_lines": int(row["quantity"])
        }
        for _, row in grouped.iterrows()
    ]

    return history[-12:]


# =========================
# EMPLOYEES
# =========================
def compute_employees(lines, productivity, feedback_coef):
    capacity = productivity * SHIFT_HOURS * feedback_coef
    if capacity <= 0:
        return 0
    return ceil(lines / capacity)


# =========================
# HIST COEF
# =========================
def compute_historical_coefficient():
    file = FORECAST_DATA_DIR / "forecast_history.csv"
    if not file.exists():
        return 1.0

    df = pd.read_csv(file)
    if df.empty:
        return 1.0

    if "real_lines" not in df or "forecast_lines" not in df:
        return 1.0

    total_forecast = df["forecast_lines"].sum()
    if total_forecast == 0:
        return 1.0

    return df["real_lines"].sum() / total_forecast