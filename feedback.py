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
from translations import t

lang = st.session_state.get("lang", "fr")

st.title(t("Feedback", lang))

companies = load_companies()

if not companies:
    st.error(t("Aucune entreprise enregistrée", lang))
    st.stop()

# =========================
# INPUTS
# =========================

col1, col2 = st.columns(2)

with col1:
    company = st.selectbox(t("Entreprise", lang), companies)

with col2:
    date = st.date_input(t("Date de début de semaine", lang))

# =========================
# CHECK IF FEEDBACK ALREADY EXISTS
# =========================

feedback_already_given = False

if FEEDBACK_FILE.exists():
    fb_df = pd.read_csv(FEEDBACK_FILE)
    if not fb_df.empty:
        mask = (
            (fb_df["company"] == normalize_company(company)) &
            (fb_df["date"] == str(date))
        )
        if mask.any():
            feedback_already_given = True

# =========================
# SHOW SIMULATION IF EXISTS
# =========================

st.markdown("---")

simulations = get_simulation_for_date(company, date)

if simulations:
    st.subheader(t("Simulation trouvée pour cette semaine", lang))

    for sim in simulations:
        with st.container():
            cols = st.columns([2, 2, 2, 2, 3])
            cols[0].metric(t("Pole", lang), sim["pole"])
            cols[1].metric(t("Employés recommandés", lang), sim["employees_recommended"])
            cols[2].metric(t("Coefficient IA", lang), f"{sim['ai_coef']:.2f}")
            cols[3].metric(t("Confiance", lang), f"{sim['confidence']:.2f}")
            created_dt = pd.to_datetime(sim["created_at"])
            cols[4].metric(t("Créé le", lang), created_dt.strftime("%Y/%m/%d %H:%M"))
        st.markdown("---")

    simulation_exists = True
else:
    st.info(t("Aucune simulation trouvée pour cette date et cette entreprise.", lang))
    simulation_exists = False

# =========================
# BLOCK IF ALREADY SUBMITTED
# =========================

if feedback_already_given:
    st.warning(t("Un feedback a déjà été soumis pour cette entreprise à cette date.", lang))

    with st.expander(t("Gerer les feedbacks", lang)):

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
                counted = t("Oui", lang) if row.get("counts") else t("Non", lang)
                real_staff = row.get("real_staff", "N/A")

                st.markdown(
                    f"**{t('Statut', lang)} :** {status_display} | "
                    f"**{t('Comptabilisé', lang)} :** {counted} | "
                    f"**{t('Effectif reel', lang)} :** {real_staff} | "
                    f"**{t('Soumis le', lang)} :** {submitted_str}"
                )

            with col_delete:
                if st.button(t("Supprimer", lang), key=f"delete_fb_{idx}", use_container_width=True):
                    fb_df = fb_df.drop(idx)
                    fb_df.to_csv(FEEDBACK_FILE, index=False)
                    st.success(t("Feedback supprime.", lang))
                    st.rerun()

    st.stop()

# =========================
# FEEDBACK FORM
# =========================

st.subheader(t("Soumettre un feedback", lang))

status_options = [
    "OK — " + t("La semaine s'est bien passée", lang),
    "KO_EXTERNE — " + t("Problème du à un évenement externe", lang),
    "KO_SUIVI — " + t("Problème, mais l'équipe a suivi la recommandation", lang),
    "KO_NON_SUIVI — " + t("Problème, l'équipe n'a PAS suivi la recommandation", lang),
]

status = st.selectbox(t("Comment s'est passée la semaine ?", lang), status_options)

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
        reason_no_count = t("Semaine OK mais aucune simulation n'existait — rien à valider.", lang)

elif status_key == "KO_EXTERNE":
    reason_no_count = t("Evenement externe — non représentatif.", lang)

elif status_key == "KO_SUIVI":
    if simulation_exists:
        counts = True
    else:
        reason_no_count = t("Aucune simulation n'existait pour cette date.", lang)

elif status_key == "KO_NON_SUIVI":
    reason_no_count = t("L'équipe n'a pas suivi la recommandation — impossible d'évaluer le modèle.", lang)

# =========================
# DISPLAY IMPACT PREVIEW
# =========================

if counts:
    if status_key == "OK":
        st.success(t("Ce feedback impactera positivement le modèle (recommandation correcte).", lang))
    elif status_key == "KO_SUIVI":
        st.warning(t("Ce feedback impactera négativement le modèle (recommandation suivie mais insuffisante).", lang))
else:
    st.info(f"{t('Ce feedback ne modifiera pas les coefficients.', lang)} {reason_no_count}")

# =========================
# OPTIONAL: REAL STAFF USED
# =========================

real_staff = None
if status_key == "KO_SUIVI":
    real_staff = st.number_input(
        t("Combien d'employés étaient réellement nécessaires ?", lang),
        min_value=0,
        value=0
    )

# =========================
# SUBMIT
# =========================

if st.button(t("Soumettre le feedback", lang), use_container_width=True):

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
        st.success(t("Feedback enregistré et coefficients mis à jour.", lang))
    else:
        st.success(t("Feedback enregistré (coefficients inchangés).", lang))

    st.rerun()