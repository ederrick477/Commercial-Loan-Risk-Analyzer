from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from .calculations import NOIInputs, compute_noi, annual_debt_service, compute_dscr, compute_ltv, compute_collateral_coverage
from .models import Loan
from .pd_model import PDModel
from .grading import grade_and_recommend
from . import repositories as repo


def assess_loan(session: Session, loan_id: int, as_of: date | None = None, notes: str | None = None) -> int:
	as_of_date = as_of or date.today()
	loan: Loan | None = repo.get_loan(session, loan_id)
	if loan is None:
		raise ValueError(f"Loan {loan_id} not found")
	fin = repo.latest_financials_for_borrower(session, loan.borrower_id)
	if fin is None:
		raise ValueError("No financials found for borrower")
	noi = compute_noi(
		NOIInputs(
			revenue=fin.revenue,
			operating_expenses=fin.operating_expenses,
			other_income=fin.other_income,
			taxes=fin.taxes,
			capex=fin.capex,
			depreciation_amortization=fin.depreciation_amortization,
		)
	)
	ads = annual_debt_service(loan.amount, loan.interest_rate, loan.amortization_months)
	dscr = compute_dscr(noi, ads)
	appraised_total, haircut_total = repo.total_collateral_values_for_loan(session, loan.loan_id)
	ltv = compute_ltv(loan.amount, appraised_total)
	coverage = compute_collateral_coverage(haircut_total, loan.amount)
	pd = PDModel().predict(dscr, ltv, coverage)
	grade, rec = grade_and_recommend(dscr, ltv, pd)
	ra = repo.record_assessment(
		session,
		loan_id=loan.loan_id,
		as_of_date=as_of_date,
		dscr=dscr,
		ltv=ltv,
		coverage=coverage,
		pd=pd,
		grade=grade,
		recommendation=rec,
		notes=notes,
		config_version="default",
	)
	return ra.assessment_id
