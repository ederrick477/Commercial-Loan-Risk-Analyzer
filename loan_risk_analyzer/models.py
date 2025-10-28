from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import String, Date, DateTime, Float, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
	pass


class Borrower(Base):
	__tablename__ = "borrowers"

	borrower_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
	industry: Mapped[Optional[str]] = mapped_column(String(100))
	state: Mapped[Optional[str]] = mapped_column(String(2))
	size_band: Mapped[Optional[str]] = mapped_column(String(50))
	created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

	loans: Mapped[List["Loan"]] = relationship(back_populates="borrower", cascade="all, delete-orphan")
	financials: Mapped[List["Financials"]] = relationship(back_populates="borrower", cascade="all, delete-orphan")
	collateral: Mapped[List["Collateral"]] = relationship(back_populates="borrower", cascade="all, delete-orphan")


class Loan(Base):
	__tablename__ = "loans"

	loan_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	borrower_id: Mapped[int] = mapped_column(ForeignKey("borrowers.borrower_id"), nullable=False)
	amount: Mapped[float] = mapped_column(Float, nullable=False)
	interest_rate: Mapped[float] = mapped_column(Float, nullable=False)  # annual decimal e.g., 0.07
	term_months: Mapped[int] = mapped_column(Integer, nullable=False)
	amortization_months: Mapped[Optional[int]] = mapped_column(Integer)  # None/0 => interest-only
	origination_date: Mapped[Optional[date]] = mapped_column(Date)
	purpose: Mapped[Optional[str]] = mapped_column(Text)
	status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

	borrower: Mapped[Borrower] = relationship(back_populates="loans")
	assessments: Mapped[List["RiskAssessment"]] = relationship(back_populates="loan", cascade="all, delete-orphan")
	pledges: Mapped[List["LoanCollateral"]] = relationship(back_populates="loan", cascade="all, delete-orphan")


class Financials(Base):
	__tablename__ = "financials"

	financial_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	borrower_id: Mapped[int] = mapped_column(ForeignKey("borrowers.borrower_id"), nullable=False)
	period_start: Mapped[date] = mapped_column(Date, nullable=False)
	period_end: Mapped[date] = mapped_column(Date, nullable=False)
	revenue: Mapped[float] = mapped_column(Float, nullable=False)
	operating_expenses: Mapped[float] = mapped_column(Float, nullable=False)
	interest_expense: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
	capex: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
	taxes: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
	other_income: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
	depreciation_amortization: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

	borrower: Mapped[Borrower] = relationship(back_populates="financials")

	__table_args__ = (
		UniqueConstraint("borrower_id", "period_end", name="uq_financials_borrower_period"),
	)


class Collateral(Base):
	__tablename__ = "collateral"

	collateral_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	borrower_id: Mapped[int] = mapped_column(ForeignKey("borrowers.borrower_id"), nullable=False)
	type: Mapped[str] = mapped_column(String(50), nullable=False)
	appraised_value: Mapped[float] = mapped_column(Float, nullable=False)
	appraisal_date: Mapped[date] = mapped_column(Date, nullable=False)
	haircut_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

	borrower: Mapped[Borrower] = relationship(back_populates="collateral")
	pledges: Mapped[List["LoanCollateral"]] = relationship(back_populates="collateral", cascade="all, delete-orphan")


class LoanCollateral(Base):
	__tablename__ = "loan_collateral"

	loan_id: Mapped[int] = mapped_column(ForeignKey("loans.loan_id"), primary_key=True)
	collateral_id: Mapped[int] = mapped_column(ForeignKey("collateral.collateral_id"), primary_key=True)
	pledged_value_override: Mapped[Optional[float]] = mapped_column(Float)

	loan: Mapped[Loan] = relationship(back_populates="pledges")
	collateral: Mapped[Collateral] = relationship(back_populates="pledges")


class RiskAssessment(Base):
	__tablename__ = "risk_assessments"

	assessment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	loan_id: Mapped[int] = mapped_column(ForeignKey("loans.loan_id"), nullable=False)
	as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
	dscr: Mapped[float] = mapped_column(Float, nullable=False)
	ltv: Mapped[float] = mapped_column(Float, nullable=False)
	collateral_coverage: Mapped[float] = mapped_column(Float, nullable=False)
	pd: Mapped[float] = mapped_column(Float, nullable=False)
	risk_grade: Mapped[str] = mapped_column(String(2), nullable=False)
	recommendation: Mapped[str] = mapped_column(String(30), nullable=False)
	notes: Mapped[Optional[str]] = mapped_column(Text)
	config_version: Mapped[Optional[str]] = mapped_column(String(100))

	loan: Mapped[Loan] = relationship(back_populates="assessments")
