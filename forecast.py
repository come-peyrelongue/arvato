import streamlit as st
import pandas as pd
from pathlib import Path
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
    save_simulation,
    get_simulation_for_date,
    normalize_company,
    SIMULATION_FILE,
    POLES
)
from translations import t

lang = st.session_state.get("lang", "fr")

# =========================
# CONFIG
# =========================

CONFIG_FILE = Path(__file__).resolve().parent / "config.json"

def load_config():
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text())

# =========================
# GEMINI SETUP
# =========================

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except:
    GOOGLE_AI_AVAILABLE = False


def init_model():
    if not GOOGLE_AI_AVAILABLE:
        return None

    config = load_config()
    api_key = config.get("GOOGLE_API_KEY", "")

    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        st.warning(f"Erreur init Gemini: {e}")
        return None


# =========================
# AI FUNCTION
# =========================

def get_ai_coef(company, pole, hist_pole, hist_all, target_date):
    if not hist_pole and not hist_all:
        return 1.0, "Aucune donnée historique disponible", "Donnés insuffisantes", 0.0

    model = init_model()
    if not model:
        return 1.0, "IA désactivée", "IA non disponible", 0.0

    current_month = pd.to_datetime(target_date).strftime("%B")
    current_period = pd.to_datetime(target_date).to_period("M")

    years_pole = set()
    for h in hist_pole:
        years_pole.add(h["period"][:4])

    years_all = set()
    for h in hist_all:
        years_all.add(h["period"][:4])

    num_months_pole = len(hist_pole)
    num_months_all = len(hist_all)
    num_years_all = len(years_all)

    response_lang = "en francais" if lang == "fr" else "in English"

    prompt = f"""
Tu es un expert en prévision de chaine logistique.

Entreprise : {company}
Pole : {pole}
Période de prévision : {current_period} ({current_month})

== données SPECIFIQUES AU POLE ({pole}) — {num_months_pole} mois, années : {', '.join(sorted(years_pole)) if years_pole else 'aucune'} ==
{json.dumps(hist_pole, indent=2)}

== TOUS POLES CONFONDUS (contexte) — {num_months_all} mois couvrant {num_years_all} années ({', '.join(sorted(years_all))}) ==
{json.dumps(hist_all, indent=2)}

INSTRUCTIONS :
1. Utilise les données specifiques au pole comme source principale de saisonnalite.
2. Utilise les données tous poles confondus comme contexte secondaire.
3. Calcule un coefficient de saisonnalite pour {current_month}.
4. Guide de confiance :
   - 0.8-1.0 : le même mois existe sur 3+ années dans les données du pole
   - 0.6-0.8 : le même mois existe sur 2+ années OU pattern fort dans tous poles
   - 0.4-0.6 : données limitées mais tendance saisonniere claire
   - 0.2-0.4 : données très éparses
   - Si tu as 2+ années de données avec un pattern cohérent, la confiance doit être au moins 0.6

Reponds UNIQUEMENT avec un JSON valide, et ecris la raison {response_lang} :
{{
  "coefficient": 1.0,
  "confidence": 0.85,
  "reason": "explication courte {response_lang}"
}}
"""

    try:
        res = model.generate_content(prompt)
        text = res.text

        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return 1.0, "format incorrect", "Erreur de parsing", 0.0

        data = json.loads(m.group())

        coef = float(data.get("coefficient", 1.0))
        reason = data.get("reason", "Analyse IA")
        confidence = float(data.get("confidence", 0.5))

        confidence = max(0.0, min(confidence, 1.0))

        return coef, reason, "Ajustement saisonnier IA appliqué", confidence

    except Exception as e:
        return 1.0, str(e), "Erreur IA", 0.0


# =========================
# SIMULATION
# =========================

def simulate_week(company, pole, start_date, total_lines):

    prod = load_productivity(company).get(pole, 120)
    hist_coef = compute_historical_coefficient()
    feedback = get_feedback_coefficient(company)

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

st.title(t("Simulation", lang))

companies = load_companies()

if not companies:
    st.error(t("Aucune entreprise trouvée ou fichier vide", lang))
    st.stop()

col1, col2 = st.columns(2)

with col1:
    company = st.selectbox(t("Entreprise", lang), companies)

with col2:
    pole = st.selectbox(t("Pôle", lang), POLES)

col3, col4 = st.columns(2)

with col3:
    start_date = st.date_input(t("Début de semaine", lang))

with col4:
    total_lines = st.number_input(
        t("Lignes prévues mensuelles", lang),
        min_value=0,
        value=0
    )

# =========================
# CHECK IF SIMULATION ALREADY EXISTS
# =========================

simulation_already_exists = False
existing_simulations = get_simulation_for_date(company, start_date)

if existing_simulations:
    # Filter by pole too
    matching = [s for s in existing_simulations if s.get("pole") == pole]
    if matching:
        simulation_already_exists = True

st.markdown("---")

if simulation_already_exists:
    st.warning(t("Une simulation existe déjà pour cette entreprise, ce pôle et cette date.", lang))

    with st.expander(t("Gérer les simulations", lang)):

        sim_df = pd.read_csv(SIMULATION_FILE)
        sim_df["start_date"] = pd.to_datetime(sim_df["start_date"], errors="coerce").dt.date

        mask = (
            (sim_df["company"] == normalize_company(company)) &
            (sim_df["start_date"] == pd.to_datetime(start_date).date()) &
            (sim_df["pole"] == pole)
        )
        existing = sim_df[mask]

        for idx in existing.index:
            row = sim_df.loc[idx]
            col_info, col_delete = st.columns([4, 1])

            with col_info:
                created = pd.to_datetime(row.get("created_at", ""), errors="coerce")
                created_str = created.strftime("%Y/%m/%d %H:%M") if pd.notna(created) else "N/A"

                st.markdown(
                    f"**{t('Pôle', lang)} :** {row.get('pole', 'N/A')} | "
                    f"**{t('Employés recommandés', lang)} :** {row.get('employees_recommended', 'N/A')} | "
                    f"**{t('Coefficient IA', lang)} :** {row.get('ai_coef', 'N/A'):.2f} | "
                    f"**{t('Confiance', lang)} :** {row.get('confidence', 'N/A'):.2f} | "
                    f"**{t('Créé le', lang)} :** {created_str}"
                )

            with col_delete:
                if st.button(t("Supprimer", lang), key=f"delete_sim_{idx}", use_container_width=True):
                    sim_df = sim_df.drop(idx)
                    sim_df.to_csv(SIMULATION_FILE, index=False)
                    st.success(t("Simulation supprimée.", lang))
                    st.rerun()

    st.stop()

# =========================
# GENERATE FORECAST
# =========================

if st.button(t("Générer la prévision", lang), use_container_width=True):

    with st.expander("Debug : données envoyées à l'IA"):
        hist_pole_debug = get_historical_data_for_ai(company, pole=pole)
        hist_all_debug = get_historical_data_for_ai(company, pole=None)

        years_pole = set(h["period"][:4] for h in hist_pole_debug)
        years_all = set(h["period"][:4] for h in hist_all_debug)

        st.write(f"**Specifique au pôle ({pole}) :** {len(hist_pole_debug)} mois, années : {sorted(years_pole)}")
        st.json(hist_pole_debug)
        st.write(f"**Tous les pôles :** {len(hist_all_debug)} mois, années : {sorted(years_all)}")
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

    save_simulation(
        company=company,
        pole=pole,
        start_date=start_date,
        employees=employees,
        adjusted_lines=adjusted_lines,
        ai_coef=ai,
        confidence=confidence
    )

    st.subheader(t("Résultat", lang))

    st.metric(t("Employés nécessaires", lang), f"{employees}")
    st.metric(t("Confiance IA", lang), f"{confidence:.2f}")

    st.progress(int(confidence * 100))

    st.write(f"### {t('Explication du calcul', lang)}")

    st.markdown(f"""
    - {t("Lignes de base", lang)} : **{total_lines}**
    - {t("Coefficient historique", lang)} : **{h:.2f}**
    - {t("Coefficient de feedback", lang)} : **{f:.2f}**
    - {t("Coefficient saisonnier IA", lang)} : **{ai:.2f}**
    - {t("Confiance IA", lang)} : **{confidence:.2f}**
    - {t("Productivite", lang)} : **{prod} {t("lignes/heure", lang)}**

    ---

    ### {t("Formule", lang)}
    $
    Lignes\\ ajustees = (Lignes \\times Hist \\times Feedback \\times IA) / 4
    $
    $
    Employes = ceil(Lignes\\ ajustees / (Productivite \\times 7h))
    $

    ---

    ### {t("Explication IA", lang)}
    {reason}

    ---

    ### {t("Note systeme", lang)}
    {explain}
    """)