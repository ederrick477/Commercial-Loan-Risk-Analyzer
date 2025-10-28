from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import csv
import typer
from rich import print
from rich.table import Table

from .db import init_db, get_session
from . import repositories as repo
from .services import assess_loan

app = typer.Typer(no_args_is_help=True)


@app.command()
def initdb() -> None:
	"""Create database tables."""
	init_db()
	print("[green]Database initialized.[/green]")


@app.command()
def seed() -> None:
	"""Seed demo data."""
	from .seed import seed_sample_data
	with get_session() as session:
		seed_sample_data(session)
	print("[green]Seeded sample data.[/green]")


@app.command("deal-new")
def deal_new(
	name: str = typer.Option(..., prompt=True),
	industry: Optional[str] = typer.Option(None, prompt=False),
	state: Optional[str] = typer.Option(None, prompt=False),
	size_band: Optional[str] = typer.Option(None, prompt=False),
	amount: float = typer.Option(..., prompt=True),
	interest_rate: float = typer.Option(..., prompt=True, help="Annual rate as decimal, e.g., 0.07"),
	term_months: int = typer.Option(..., prompt=True),
	amortization_months: Optional[int] = typer.Option(None, prompt=True),
	purpose: Optional[str] = typer.Option(None, prompt=False),
	revenue: float = typer.Option(..., prompt=True),
	operating_expenses: float = typer.Option(..., prompt=True),
	other_income: float = typer.Option(0.0, prompt=False),
	taxes: float = typer.Option(0.0, prompt=False),
	capex: float = typer.Option(0.0, prompt=False),
	depreciation_amortization: float = typer.Option(0.0, prompt=False),
	collateral_type: str = typer.Option("RealEstate", prompt=True),
	appraised_value: float = typer.Option(..., prompt=True),
	haircut_pct: float = typer.Option(0.2, prompt=True),
) -> None:
	with get_session() as session:
		b = repo.get_or_create_borrower(session, name, industry, state, size_band)
		loan = repo.create_loan(session, b.borrower_id, amount, interest_rate, term_months, amortization_months, date.today(), purpose)
		period_end = date.today()
		period_start = period_end - timedelta(days=365)
		repo.upsert_financials(
			session,
			b.borrower_id,
			period_start=period_start,
			period_end=period_end,
			revenue=revenue,
			operating_expenses=operating_expenses,
			other_income=other_income,
			taxes=taxes,
			capex=capex,
			depreciation_amortization=depreciation_amortization,
		)
		col = repo.add_collateral(session, b.borrower_id, collateral_type, appraised_value, date.today(), haircut_pct)
		repo.link_loan_collateral(session, loan.loan_id, col.collateral_id)
		print(f"[green]Created loan {loan.loan_id} for {b.name}.[/green]")


@app.command("loan-list")
def loan_list() -> None:
	with get_session() as session:
		loans = repo.list_active_loans(session)
		t = Table(title="Active Loans")
		t.add_column("Loan ID")
		t.add_column("Borrower")
		t.add_column("Amount")
		t.add_column("Rate")
		t.add_column("Term")
		for ln in loans:
			t.add_row(str(ln.loan_id), ln.borrower.name, f"{ln.amount:,.0f}", f"{ln.interest_rate:.2%}", f"{ln.term_months}")
		print(t)


@app.command("assess")
def assess(loan_id: int = typer.Argument(...)) -> None:
	with get_session() as session:
		ra_id = assess_loan(session, loan_id)
		ra = repo.latest_assessment_for_loan(session, loan_id)
		print(f"[green]Assessed loan {loan_id}, assessment {ra_id}.[/green]")
		if ra:
			print(f"DSCR={ra.dscr:.2f} LTV={ra.ltv:.2f} Coverage={ra.collateral_coverage:.2f} PD={ra.pd:.2%} Grade={ra.risk_grade} {ra.recommendation}")


@app.command("portfolio-summary")
def portfolio_summary() -> None:
	with get_session() as session:
		loans = repo.list_active_loans(session)
		t = Table(title="Portfolio Summary")
		t.add_column("Metric")
		t.add_column("Value")
		total_exposure = sum(l.amount for l in loans)
		t.add_row("Total Exposure", f"{total_exposure:,.0f}")
		dscrs = []
		ltvs = []
		pds = []
		grades: dict[str, int] = {}
		for ln in loans:
			ra = repo.latest_assessment_for_loan(session, ln.loan_id)
			if ra:
				dscrs.append(ra.dscr)
				ltvs.append(ra.ltv)
				pds.append(ra.pd)
				grades[ra.risk_grade] = grades.get(ra.risk_grade, 0) + 1
		if dscrs:
			t.add_row("Avg DSCR", f"{sum(dscrs)/len(dscrs):.2f}")
		if ltvs:
			t.add_row("Avg LTV", f"{sum(ltvs)/len(ltvs):.2f}")
		if pds:
			t.add_row("Avg PD", f"{sum(pds)/len(pds):.2%}")
		for g, n in sorted(grades.items()):
			t.add_row(f"Count {g}", str(n))
		print(t)


@app.command("export-deals")
def export_deals(out: Path = typer.Option(Path("deals.csv"))) -> None:
	with get_session() as session:
		loans = repo.list_active_loans(session)
		with out.open("w", newline="") as f:
			writer = csv.writer(f)
			writer.writerow(["loan_id", "borrower", "amount", "rate", "term", "dscr", "ltv", "coverage", "pd", "grade", "recommendation"])
			for ln in loans:
				ra = repo.latest_assessment_for_loan(session, ln.loan_id)
				writer.writerow([
					ln.loan_id,
					ln.borrower.name,
					ln.amount,
					ln.interest_rate,
					ln.term_months,
					getattr(ra, "dscr", None),
					getattr(ra, "ltv", None),
					getattr(ra, "collateral_coverage", None),
					getattr(ra, "pd", None),
					getattr(ra, "risk_grade", None),
					getattr(ra, "recommendation", None),
				])
	print(f"[green]Exported to {out}[/green]")


if __name__ == "__main__":
	app()
