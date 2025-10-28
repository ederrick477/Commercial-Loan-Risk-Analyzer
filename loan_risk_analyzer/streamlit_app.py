from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from loan_risk_analyzer.db import init_db, get_session
from loan_risk_analyzer import repositories as repo
from loan_risk_analyzer.services import assess_loan

st.set_page_config(page_title="Commercial Loan Risk Analyzer", layout="wide")

st.title("Commercial Loan Risk Analyzer")

init_db()

tabs = st.tabs(["Deal Input", "Loan Detail", "Portfolio Dashboard"])

with tabs[0]:
	st.subheader("New Deal")
	with st.form("deal_form"):
		col1, col2, col3 = st.columns(3)
		with col1:
			name = st.text_input("Borrower Name", "Acme Manufacturing")
			industry = st.text_input("Industry", "Manufacturing")
			state = st.text_input("State", "CA")
			size_band = st.text_input("Size Band", "Mid")
		with col2:
			amount = st.number_input("Loan Amount", min_value=0.0, value=2_000_000.0, step=10000.0)
			interest_rate = st.number_input("Interest Rate (decimal)", min_value=0.0, max_value=1.0, value=0.07, step=0.005)
			term_months = st.number_input("Term (months)", min_value=1, value=60, step=1)
			amortization_months = st.number_input("Amortization (months, 0=IO)", min_value=0, value=240, step=1)
		with col3:
			revenue = st.number_input("Revenue", min_value=0.0, value=5_000_000.0, step=10000.0)
			operating_expenses = st.number_input("Operating Expenses", min_value=0.0, value=3_200_000.0, step=10000.0)
			other_income = st.number_input("Other Income", min_value=0.0, value=50_000.0, step=1000.0)
			taxes = st.number_input("Taxes", min_value=0.0, value=200_000.0, step=1000.0)
			capex = st.number_input("CapEx", min_value=0.0, value=150_000.0, step=1000.0)
			depreciation_amortization = st.number_input("Depreciation + Amortization", min_value=0.0, value=180_000.0, step=1000.0)
		colx, coly = st.columns(2)
		with colx:
			collateral_type = st.text_input("Collateral Type", "RealEstate")
			appraised_value = st.number_input("Appraised Value", min_value=0.0, value=3_000_000.0, step=10000.0)
		with coly:
			haircut_pct = st.number_input("Haircut (decimal)", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
		submitted = st.form_submit_button("Create Deal & Assess")
	if submitted:
		with get_session() as session:
			b = repo.get_or_create_borrower(session, name, industry, state, size_band)
			loan = repo.create_loan(session, b.borrower_id, amount, interest_rate, int(term_months), int(amortization_months), date.today(), "")
			period_end = date.today()
			period_start = period_end - timedelta(days=365)
			repo.upsert_financials(session, b.borrower_id, period_start=period_start, period_end=period_end, revenue=revenue, operating_expenses=operating_expenses, other_income=other_income, taxes=taxes, capex=capex, depreciation_amortization=depreciation_amortization)
			col = repo.add_collateral(session, b.borrower_id, collateral_type, appraised_value, date.today(), haircut_pct)
			repo.link_loan_collateral(session, loan.loan_id, col.collateral_id)
			ra_id = assess_loan(session, loan.loan_id)
			st.success(f"Created and assessed loan {loan.loan_id} (assessment {ra_id}).")

with tabs[1]:
	st.subheader("Loan Detail")
	with get_session() as session:
		loans = repo.list_active_loans(session)
		loan_map = {f"{ln.loan_id} - {ln.borrower.name}": ln for ln in loans}
		if loan_map:
			choice = st.selectbox("Select Loan", list(loan_map.keys()))
			ln = loan_map[choice]
			ra = repo.latest_assessment_for_loan(session, ln.loan_id)
			if ra:
				c1, c2, c3, c4, c5 = st.columns(5)
				c1.metric("DSCR", f"{ra.dscr:.2f}")
				c2.metric("LTV", f"{ra.ltv:.2f}")
				c3.metric("Coverage", f"{ra.collateral_coverage:.2f}")
				c4.metric("PD", f"{ra.pd:.2%}")
				c5.metric("Grade", ra.risk_grade)
				st.write(ra.recommendation)
			else:
				st.info("No assessment yet for selected loan.")
		else:
			st.info("No active loans.")

with tabs[2]:
	st.subheader("Portfolio Dashboard")
	with get_session() as session:
		loans = repo.list_active_loans(session)
		records = []
		for ln in loans:
			ra = repo.latest_assessment_for_loan(session, ln.loan_id)
			if ra:
				records.append({
					"loan_id": ln.loan_id,
					"borrower": ln.borrower.name,
					"amount": ln.amount,
					"dscr": ra.dscr,
					"ltv": ra.ltv,
					"pd": ra.pd,
					"grade": ra.risk_grade,
				})
		if records:
			df = pd.DataFrame(records)
			c1, c2 = st.columns(2)
			chart1 = alt.Chart(df).mark_bar().encode(x=alt.X("dscr", bin=alt.Bin(maxbins=20)), y="count()")
			c1.altair_chart(chart1, use_container_width=True)
			chart2 = alt.Chart(df).mark_bar().encode(x=alt.X("ltv", bin=alt.Bin(maxbins=20)), y="count()")
			c2.altair_chart(chart2, use_container_width=True)
			chart3 = alt.Chart(df).mark_circle(size=80).encode(x="ltv", y="dscr", color="grade")
			st.altair_chart(chart3, use_container_width=True)
			st.dataframe(df)
		else:
			st.info("Assess loans to populate dashboard.")
