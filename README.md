# Staffing Forecast System

## Overview

The Staffing Forecast System is a data-driven application designed to estimate workforce requirements based on operational workload, productivity rates, and adaptive correction coefficients. It is built for logistics and operations environments where staffing needs must be forecasted dynamically using both historical and real-world feedback data.

The system provides:
- Data ingestion (real and forecast data)
- Workforce forecasting per operational pole
- Productivity management per company
- Feedback-driven model correction
- Historical accuracy adjustment through coefficients
- Company-based data isolation

---

## Technology Stack

### Backend / Core Application
- Python 3.10+
- Streamlit
- Pandas
- OpenPyXL
- JSON / CSV storage

### Optional Extensions (planned)
- FastAPI (backend API layer)
- React (frontend interface)
- Recharts (data visualization)

---

## Installation

1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Run Streamlit

---

## Run

```bash
pip install streamlit pandas openpyxl
streamlit run app.py
```

---

## System Logic

capacity = productivity × shift_hours × feedback_coefficient

adjusted_lines = monthly_lines × historical_coefficient / 4

employees = adjusted_lines / capacity

---

## Modules

- Company management
- Data ingestion
- Forecast engine
- Feedback system
- Dashboard

---

## License

* "Côme PEYRELONGUE" <come.peyrelongue@utt.fr>; 
* “Léa BAUDOUIN” <lea.baudouin@utt.fr>; 
* “Marco ORFAO” <marco.orfao@utt.fr>;
* “Victor PENUCHOT” <victor.penuchot@utt.fr>;

Internal academic project - CRUNCH 2026 UTT