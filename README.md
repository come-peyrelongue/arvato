# Staffing Forecast System — Arvato / CRUNCH 2026

A data-driven application for estimating workforce requirements based on operational workload, productivity rates, and AI-powered seasonality analysis. Built for logistics and operations environments where staffing needs must be forecasted dynamically.

---

## Features

- Company Management: Create, rename, delete companies
- Data Ingestion: Import real historical data from Excel files (multi-year support)
- AI-Powered Forecast: Workforce estimation per operational pole using Google Gemini 2.5 Flash
- Productivity Management: Configurable productivity rates per company and pole
- Feedback System: Model self-correction based on real-world outcomes
- Historical Coefficient: Automatic accuracy adjustment over time

---

## Prerequisites

### Python Version

IMPORTANT: Python 3.11 or 3.12 required.
Python 3.13+ and 3.14+ are NOT compatible with the google-generativeai package.
The AI-powered seasonality analysis will not work on newer Python versions.

Verify your version:

    python --version

### Google Gemini API Key

The system uses Google Gemini 2.5 Flash for seasonality coefficient estimation.
You need a valid API key from https://aistudio.google.com/apikey

---

## Installation

### 1. Clone the repository

    git clone https://github.com/Come-Peyrelongue/Arvato.git
    cd Arvato

### 2. Create a virtual environment

    python -m venv venv

Activate it:

Windows:

    venv\Scripts\activate

macOS / Linux:

    source venv/bin/activate

### 3. Install dependencies

    pip install streamlit pandas openpyxl google-generativeai

Or if a requirements.txt is provided:

    pip install -r requirements.txt

### 4. Configure API Key

Create a file named src/config.json:

    {
      "GOOGLE_API_KEY": "your-google-api-key-here"
    }

WARNING: This file is listed in .gitignore and must NEVER be committed.

---

## Run

    cd src
    streamlit run app.py

The application will open in your browser at http://localhost:8501

---

## Project Structure

    Arvato/
    |-- src/
    |   |-- app.py                 # Main Streamlit app (page routing)
    |   |-- utils.py               # Core logic, data functions, constants
    |   |-- forecast.py            # AI-powered workforce forecast page
    |   |-- feedback.py            # Feedback submission page
    |   |-- ingestion.py           # Data import page
    |   |-- productivity.py        # Productivity configuration page
    |   |-- companies.py           # Company management page
    |   |-- config.json            # API key (excluded from git)
    |   |-- data/
    |       |-- companies.json     # Registered companies
    |       |-- coefficients.json  # Feedback coefficients per company
    |       |-- simulations.csv    # Saved simulation history
    |       |-- feedback.csv       # Feedback history
    |       |-- real/              # Real historical data (CSV per company)
    |       |-- forecast/          # Forecast data and history
    |-- .gitignore
    |-- README.md
    |-- requirements.txt

---

## System Logic

### Forecast Formula

    adjusted_lines = (monthly_lines x historical_coef x feedback_coef x ai_seasonal_coef) / 4
    capacity = productivity x shift_hours (7h)
    employees = ceil(adjusted_lines / capacity)

### Coefficients

- Historical: from forecast_history.csv — corrects systematic over/under-estimation
- Feedback: from user feedback submissions — adjusts based on real outcomes
- AI Seasonal: from Google Gemini analysis — accounts for monthly seasonality patterns

### Operational Poles

- PICKING: 157 lines/hour (default)
- PROMO: 125 lines/hour (default)
- BULK: 26.5 lines/hour (default)
- GLOBAL: 27.6 lines/hour (default)

---

## Feedback Logic

- Week went well + simulation exists       -> Counts (strengthens coefficient)
- Week went well + no simulation           -> Does NOT count (nothing to validate)
- Problem due to external event            -> Does NOT count (not representative)
- Problem + followed recommendation        -> Counts (weakens coefficient)
- Problem + did NOT follow recommendation  -> Does NOT count (cannot evaluate model)

---

## Data Format

### Real Data (Excel to CSV)

Imported Excel files must contain these columns:

- date: Date — Activity date
- pole: String — PICKING, PROMO, BULK, or GLOBAL
- quantity: Integer — Number of lines processed
- company: String — Company identifier

The system splits data by company and stores as headerless CSV files in data/real/.

---

## Troubleshooting

- ModuleNotFoundError google.generativeai -> pip install google-generativeai
- AI returns low confidence -> Ensure multi-year data is imported (not just 1 year)
- KeyError start_date -> Delete data/simulations.csv and re-run a forecast
- Gemini does not work -> Verify Python version is 3.11 or 3.12, not 3.13+
- API key error -> Check config.json exists in src/ with valid key

---

## Authors

- Come PEYRELONGUE — come.peyrelongue@utt.fr
- Lea BAUDOUIN — lea.baudouin@utt.fr
- Marco ORFAO — marco.orfao@utt.fr
- Victor PENUCHOT — victor.penuchot@utt.fr

---

## License

Internal academic project — CRUNCH 2026, Université de Technologie de Troyes (UTT).