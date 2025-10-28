from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .models import Borrower, Loan, Financials, Collateral, LoanCollateral, RiskAssessment


def get_or_create_borrower(session: Session, name: str, industry: Optional[str], state: Optional[str], size_band: Optional[str]) -> Borrower:
	borrower = session.execute(select(Borrower).where(Borrower.name == name)).scalar_one_or_none()
	if borrower:
		return borrower
	borrower = Borrower(name=name, industry=industry, state=state, size_band=size_band)
	session.add(borrower)
	session.flush()
	return borrower


def create_loan(session: Session, borrower_id: int, amount: float, interest_rate: float, term_months: int, amortization_months: Optional[int], origination_date: Optional[date], purpose: Optional[str]) -> Loan:
	loan = Loan(
		borrower_id=borrower_id,
		amount=amount,
		interest_rate=interest_rate,
		term_months=term_months,
		amortization_months=amortization_months,
		origination_date=origination_date,
		purpose=purpose,
		status="active",
	)
	session.add(loan)
	session.flush()
	return loan


def upsert_financials(session: Session, borrower_id: int, period_start: date, period_end: date, **kwargs) -> Financials:
	row = session.execute(
		select(Financials).where(Financials.borrower_id == borrower_id, Financials.period_end == period_end)
	).scalar_one_or_none()
	if row:
		for k, v in kwargs.items():
			setattr(row, k, v)
		return row
	row = Financials(borrower_id=borrower_id, period_start=period_start, period_end=period_end, **kwargs)
	session.add(row)
	session.flush()
	return row


def add_collateral(session: Session, borrower_id: int, type: str, appraised_value: float, appraisal_date: date, haircut_pct: float) -> Collateral:
	col = Collateral(
		borrower_id=borrower_id,
		type=type,
		appraised_value=appraised_value,
		appraisal_date=appraisal_date,
		haircut_pct=haircut_pct,
	)
	session.add(col)
	session.flush()
	return col


def link_loan_collateral(session: Session, loan_id: int, collateral_id: int, pledged_value_override: Optional[float] = None) -> LoanCollateral:
	link = LoanCollateral(loan_id=loan_id, collateral_id=collateral_id, pledged_value_override=pledged_value_override)
	session.add(link)
	session.flush()
	return link


def get_loan(session: Session, loan_id: int) -> Optional[Loan]:
	return session.get(Loan, loan_id)


def list_active_loans(session: Session):
	return session.execute(select(Loan).where(Loan.status == "active")).scalars().all()


def latest_financials_for_borrower(session: Session, borrower_id: int) -> Optional[Financials]:
	return session.execute(
		select(Financials).where(Financials.borrower_id == borrower_id).order_by(Financials.period_end.desc()).limit(1)
	).scalar_one_or_none()


def total_collateral_values_for_loan(session: Session, loan_id: int) -> Tuple[float, float]:
	rows = session.execute(
		select(Collateral.appraised_value, Collateral.haircut_pct, LoanCollateral.pledged_value_override)
		.join(LoanCollateral, LoanCollateral.collateral_id == Collateral.collateral_id)
		.where(LoanCollateral.loan_id == loan_id)
	).all()
	appraised_total = 0.0
	haircut_total = 0.0
	for appraised_value, haircut_pct, override in rows:
		if override is not None:
			adj = override
		else:
			adj = appraised_value * (1.0 - haircut_pct)
		appraised_total += appraised_value
		haircut_total += adj
	return appraised_total, haircut_total


def record_assessment(session: Session, loan_id: int, as_of_date: date, dscr: float, ltv: float, coverage: float, pd: float, grade: str, recommendation: str, notes: Optional[str], config_version: Optional[str]) -> RiskAssessment:
	row = RiskAssessment(
		loan_id=loan_id,
		as_of_date=as_of_date,
		dscr=dscr,
		ltv=ltv,
		collateral_coverage=coverage,
		pd=pd,
		risk_grade=grade,
		recommendation=recommendation,
		notes=notes,
		config_version=config_version,
	)
	session.add(row)
	session.flush()
	return row


def latest_assessment_for_loan(session: Session, loan_id: int) -> Optional[RiskAssessment]:
	return session.execute(
		select(RiskAssessment)
		.where(RiskAssessment.loan_id == loan_id)
		.order_by(RiskAssessment.as_of_date.desc(), RiskAssessment.assessment_id.desc())
		.limit(1)
	).scalar_one_or_none()
