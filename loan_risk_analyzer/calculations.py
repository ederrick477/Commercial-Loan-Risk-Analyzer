from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NOIInputs:
	revenue: float
	operating_expenses: float
	other_income: float
	taxes: float
	capex: float
	depreciation_amortization: float = 0.0
	add_back_da: bool = True


def compute_noi(inputs: NOIInputs) -> float:
	noi = inputs.revenue - inputs.operating_expenses + inputs.other_income - inputs.taxes - inputs.capex
	if inputs.add_back_da:
		noi += inputs.depreciation_amortization
	return max(noi, 0.0)


def amortization_payment(principal: float, annual_rate: float, amortization_months: int | None) -> float:
	if not amortization_months or amortization_months <= 0:
		return (annual_rate / 12.0) * principal
	monthly_rate = annual_rate / 12.0
	if monthly_rate == 0:
		return principal / amortization_months
	factor = (1 + monthly_rate) ** amortization_months
	return principal * monthly_rate * factor / (factor - 1)


def annual_debt_service(principal: float, annual_rate: float, amortization_months: int | None) -> float:
	return amortization_payment(principal, annual_rate, amortization_months) * 12.0


def compute_dscr(noi: float, annual_debt_service_amount: float) -> float:
	if annual_debt_service_amount <= 0:
		return float("inf")
	return noi / annual_debt_service_amount


def compute_ltv(loan_amount: float, collateral_appraised_total: float) -> float:
	if collateral_appraised_total <= 0:
		return float("inf")
	return loan_amount / collateral_appraised_total


def compute_collateral_coverage(collateral_haircut_total: float, loan_amount: float) -> float:
	if loan_amount <= 0:
		return float("inf")
	return collateral_haircut_total / loan_amount
