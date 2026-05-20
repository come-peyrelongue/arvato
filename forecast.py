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

GOOGLE_API_KEY = "AIzaSyD997azn1C0gqEB_lIgez01qfryh_LDBks"

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

def get_ai_coef(company, hist, target_date):
    if not hist:
        return 1.0, "No historical data available", "Insufficient data", 0.0

    model = init_model()
    if not model:
        return 1.0, "AI disabled", "AI not available", 0.0

    current_month = pd.to_datetime(target_date).strftime("%B")
    current_period = pd.to_datetime(target_date).to_period("M")

    prompt = f"""
You are a supply chain forecasting expert.

Company: {company}
Forecast period: {current_period} ({current_month})

Focus ONLY on seasonality relevant to this period.

Historical data:
{json.dumps(hist, indent=2)}

TASK:
1. Determine seasonality for this period
2. Ignore irrelevant peaks (e.g. Christmas if not relevant)
3. Compute coefficient for THIS period
4. Estimate confidence (0 to 1)

Return ONLY JSON:
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

    hist = get_historical_data_for_ai(company)

    ai_coef, ai_reason, ai_explain, confidence = get_ai_coef(
        company,
        hist,
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
Adjusted Lines = (Lines × Hist × Feedback × AI) / 4  
Employees = ceil(Adjusted Lines / (Productivity × 7h shift))
$

---

### AI explanation
{reason}

---

### System note
{explain}
""")