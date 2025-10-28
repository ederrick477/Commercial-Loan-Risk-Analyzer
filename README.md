# Commercial Loan Risk Analyzer

A runnable demo that shows underwriting logic, SQLite data modeling, financial metrics (DSCR, LTV, collateral coverage), PD estimation, risk grading, reporting, and a Streamlit dashboard.

## Quick start

1) Create a virtualenv (Python 3.11 recommended) and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Initialize the database and seed sample data:

```bash
python -m loan_risk_analyzer.cli initdb
python -m loan_risk_analyzer.cli seed
python -m loan_risk_analyzer.cli loan-list
python -m loan_risk_analyzer.cli assess 1
python -m loan_risk_analyzer.cli portfolio-summary
python -m loan_risk_analyzer.cli export-deals --out deals.csv
```

3) Launch the web app:

```bash
streamlit run loan_risk_analyzer/streamlit_app.py
```

The SQLite database file `loans.db` is created in the repo root by default. Override location by setting `LOANS_DB_PATH` env var.

## Project structure

- `loan_risk_analyzer/` core package
  - `db.py` database engine and session
  - `models.py` ORM models
  - `repositories.py` CRUD and queries
  - `calculations.py` metric functions
  - `pd_model.py` PD model (config-driven)
  - `grading.py` risk grading
  - `services.py` assessment orchestration
  - `cli.py` Typer CLI
  - `streamlit_app.py` Streamlit app
- `config/` default YAML configs (`pd.yaml`, `grading.yaml`, `metrics.yaml`)
- `requirements.txt` dependencies

## Notes

- Metrics: DSCR = NOI / Annual Debt Service; LTV = Loan / Appraised Collateral; Collateral coverage uses haircut-adjusted values.
- PD: simple logistic with configurable coefficients.
- Grading: PD buckets with DSCR/LTV guardrails.
