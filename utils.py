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


def save_companies(companies):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COMPANIES_FILE.write_text(json.dumps(companies, indent=2))

# =========================
# INGESTION
# =========================
def split_and_store(df, mode="real"):
    """
    Splits uploaded data by company and APPENDS to existing CSVs.
    Expected columns in df: date, pole, quantity, company (or similar).
    """
    target_dir = REAL_DATA_DIR if mode == "real" else FORECAST_DATA_DIR

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Detect company column (adjust based on your Excel structure)
    if "company" in df.columns:
        group_col = "company"
    else:
        # If no company column, ask user or use filename
        group_col = None

    if group_col:
        for company, group in df.groupby(group_col):
            company_norm = normalize_company(company)
            path = target_dir / f"{company_norm}.csv"

            # Keep only relevant columns
            export_cols = [c for c in ["date", "pole", "quantity"] if c in group.columns]
            group = group[export_cols].copy()

            # Clean data
            group["date"] = pd.to_datetime(group["date"], errors="coerce")
            group = group.dropna(subset=["date"])
            group["pole"] = group["pole"].astype(str).str.strip().str.upper()
            group["quantity"] = pd.to_numeric(group["quantity"], errors="coerce").fillna(0).astype(int)

            # APPEND if file exists, otherwise create
            if path.exists():
                df_existing = pd.read_csv(path, header=None, names=["date", "pole", "quantity"])
                df_existing["date"] = pd.to_datetime(df_existing["date"], errors="coerce")
                df_combined = pd.concat([df_existing, group], ignore_index=True)
                # Remove exact duplicates
                df_combined = df_combined.drop_duplicates(subset=["date", "pole", "quantity"])
                df_combined = df_combined.sort_values("date")
            else:
                df_combined = group.sort_values("date")

            df_combined.to_csv(path, index=False, header=False)
    else:
        # No company column — save everything to a single file
        path = target_dir / "all_data.csv"
        df.to_csv(path, mode="a", index=False, header=not path.exists())


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


def save_productivity(company, prod):
    path = productivity_file(company)
    path.write_text(json.dumps(prod, indent=2))


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
def get_historical_data_for_ai(company, pole=None):
    """
    Returns ALL monthly history, regardless of CSV format.
    """
    company = normalize_company(company)

    file_candidates = [
        REAL_DATA_DIR / f"{company}.csv",
        REAL_DATA_DIR / f"{company.lower()}.csv",
    ]

    df = None
    for f in file_candidates:
        if f.exists():
            # TOUJOURS lire sans header et forcer les noms de colonnes
            df = pd.read_csv(
                f,
                header=None,
                names=["date", "pole", "quantity"],
                dtype=str  # Lire tout en string d'abord
            )
            break

    if df is None or df.empty:
        return []

    # Convertir les dates — les lignes invalides (headers dupliqués, etc.) deviennent NaT
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # Nettoyer pole
    df["pole"] = df["pole"].str.strip().str.upper()

    # Convertir quantity en numérique
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)

    # Filter by pole if specified
    if pole:
        df = df[df["pole"] == pole.strip().upper()]

    if df.empty:
        return []

    df["month"] = df["date"].dt.to_period("M").astype(str)

    grouped = df.groupby("month")["quantity"].sum().reset_index()

    history = [
        {
            "period": row["month"],
            "real_lines": int(row["quantity"])
        }
        for _, row in grouped.iterrows()
    ]

    return history

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