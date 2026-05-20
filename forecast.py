import streamlit as st
import pandas as pd
from datetime import timedelta
import re
import json

from utils import (
    load_companies,
    load_productivity,
    get_feedback_coefficient,
    compute_historical_coefficient,
    compute_employees,
    get_historical_data_for_ai,
    POLES
)

# =========================
# GEMINI SETUP
# =========================

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except:
    GOOGLE_AI_AVAILABLE = False

GOOGLE_API_KEY = "AIzaSyAIJnREhIXOZfMWLEUsBeSXtbW6nzSNaaU"

def init_model():
    if not GOOGLE_AI_AVAILABLE:
        return None

    if not GOOGLE_API_KEY or "YOUR" in GOOGLE_API_KEY:
        return None

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        st.warning(f"Gemini init error: {e}")
        return None


# =========================
# AI FUNCTION
# =========================

def get_ai_coef(company, pole, hist_pole, hist_all, target_date):
    """
    company: company name
    pole: pole being forecasted
    hist_pole: monthly history filtered by pole
    hist_all: monthly history for ALL poles (context)
    target_date: date being forecasted
    """
    if not hist_pole and not hist_all:
        return 1.0, "No historical data available", "Insufficient data", 0.0

    model = init_model()
    if not model:
        return 1.0, "AI disabled", "AI not available", 0.0

    current_month = pd.to_datetime(target_date).strftime("%B")
    current_period = pd.to_datetime(target_date).to_period("M")

    # Compute coverage info for pole-specific data
    years_pole = set()
    for h in hist_pole:
        years_pole.add(h["period"][:4])

    # Compute coverage info for all data
    years_all = set()
    for h in hist_all:
        years_all.add(h["period"][:4])

    num_months_pole = len(hist_pole)
    num_months_all = len(hist_all)
    num_years_all = len(years_all)

    prompt = f"""
You are a supply chain forecasting expert.

Company: {company}
Pole: {pole}
Forecast period: {current_period} ({current_month})

== POLE-SPECIFIC DATA ({pole}) — {num_months_pole} months, years: {', '.join(sorted(years_pole)) if years_pole else 'none'} ==
{json.dumps(hist_pole, indent=2)}

== ALL POLES COMBINED (context) — {num_months_all} months spanning {num_years_all} years ({', '.join(sorted(years_all))}) ==
{json.dumps(hist_all, indent=2)}

INSTRUCTIONS:
1. Use pole-specific data as primary source for seasonality.
2. Use all-poles data as secondary context to infer general seasonal patterns.
3. Compute a seasonality coefficient for {current_month}.
4. Confidence guidelines:
   - 0.8–1.0: same month exists across 3+ years in pole data
   - 0.6–0.8: same month exists across 2+ years OR strong pattern in all-poles data
   - 0.4–0.6: limited pole data but clear overall seasonal trend
   - 0.2–0.4: very sparse data, mostly guessing
   - If you have 2+ years of ANY data showing a consistent pattern, confidence should be at least 0.6

Return ONLY valid JSON:
{{
  "coefficient": 1.0,
  "confidence": 0.85,
  "reason": "short explanation in English"
}}
"""

    try:
        res = model.generate_content(prompt)
        text = res.text

        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return 1.0, "bad format", "Parsing error", 0.0

        data = json.loads(m.group())

        coef = float(data.get("coefficient", 1.0))
        reason = data.get("reason", "AI analysis")
        confidence = float(data.get("confidence", 0.5))

        confidence = max(0.0, min(confidence, 1.0))

        return coef, reason, "AI seasonal adjustment applied ✅", confidence

    except Exception as e:
        return 1.0, str(e), "AI error ❌", 0.0


# =========================
# SIMULATION
# =========================

def simulate_week(company, pole, start_date, total_lines):

    prod = load_productivity(company).get(pole, 120)
    hist_coef = compute_historical_coefficient()
    feedback = get_feedback_coefficient(company)

    # Get pole-specific AND all-poles history
    hist_pole = get_historical_data_for_ai(company, pole=pole)
    hist_all = get_historical_data_for_ai(company, pole=None)

    ai_coef, ai_reason, ai_explain, confidence = get_ai_coef(
        company,
        pole,
        hist_pole,
        hist_all,
        start_date
    )

    adjusted_lines = (total_lines * hist_coef * feedback * ai_coef) / 4

    employees = compute_employees(adjusted_lines, prod, 1.0)

    return (
        employees,
        adjusted_lines,
        prod,
        hist_coef,
        feedback,
        ai_coef,
        ai_reason,
        ai_explain,
        confidence
    )


# =========================
# UI
# =========================

st.title("Forecast")

companies = load_companies()

if not companies:
    st.error("No companies.json found or empty")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    company = st.selectbox("Company", companies)

with col2:
    pole = st.selectbox("Pole", POLES)

col3, col4 = st.columns(2)

with col3:
    start_date = st.date_input("Start week")

with col4:
    total_lines = st.number_input(
        "Monthly forecast lines",
        min_value=0,
        value=0
    )

if st.button("Generate Forecast", use_container_width=True):

    # DEBUG: show what data the AI receives
    with st.expander("🔍 Debug: Data sent to AI"):
        hist_pole_debug = get_historical_data_for_ai(company, pole=pole)
        hist_all_debug = get_historical_data_for_ai(company, pole=None)
    
        # Stats clés
        years_pole = set(h["period"][:4] for h in hist_pole_debug)
        years_all = set(h["period"][:4] for h in hist_all_debug)
        
        st.write(f"**Pole-specific ({pole}):** {len(hist_pole_debug)} months, years: {sorted(years_pole)}")
        st.json(hist_pole_debug)
        st.write(f"**All poles:** {len(hist_all_debug)} months, years: {sorted(years_all)}")
        st.json(hist_all_debug)

    (
        employees,
        adjusted_lines,
        prod,
        h,
        f,
        ai,
        reason,
        explain,
        confidence
    ) = simulate_week(
        company,
        pole,
        pd.to_datetime(start_date),
        total_lines
    )

    st.subheader("Result")

    st.metric("Employees required", f"{employees}")
    st.metric("AI Confidence", f"{confidence:.2f}")

    st.progress(int(confidence * 100))

    st.write("### Calculation explanation")

    st.markdown(f"""
- Base lines: **{total_lines}**
- Historical coefficient: **{h:.2f}**
- Feedback coefficient: **{f:.2f}**
- AI seasonal coefficient: **{ai:.2f}**
- AI confidence: **{confidence:.2f}**
- Productivity: **{prod} lines/hour**

---

### Formula
$
Adjusted\\ Lines = (Lines × Hist × Feedback × AI) / 4  
$
$
Employees = ceil(Adjusted\\ Lines / (Productivity × 7h\\ shift))
$

---

### AI explanation
{reason}

---

### System note
{explain}
""")