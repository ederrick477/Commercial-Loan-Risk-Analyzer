from __future__ import annotations

from datetime import date, timedelta
from sqlalchemy.orm import Session

from . import repositories as repo


def seed_sample_data(session: Session) -> None:
	b = repo.get_or_create_borrower(session, name="Acme Manufacturing", industry="Manufacturing", state="CA", size_band="Mid")
	loan = repo.create_loan(session, b.borrower_id, amount=2_000_000, interest_rate=0.07, term_months=60, amortization_months=240, origination_date=date.today(), purpose="Equipment + WC")
	period_end = date.today()
	period_start = period_end - timedelta(days=365)
	repo.upsert_financials(
		session,
		b.borrower_id,
		period_start=period_start,
		period_end=period_end,
		revenue=5_000_000,
		operating_expenses=3_200_000,
		other_income=50_000,
		taxes=200_000,
		capex=150_000,
		depreciation_amortization=180_000,
	)
	col1 = repo.add_collateral(session, b.borrower_id, type="RealEstate", appraised_value=3_000_000, appraisal_date=date.today(), haircut_pct=0.2)
	repo.link_loan_collateral(session, loan.loan_id, col1.collateral_id)
