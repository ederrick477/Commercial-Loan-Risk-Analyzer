from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class GradeRule:
	grade: str
	max_pd: float
	min_dscr: float
	max_ltv: float


@dataclass
class GradingConfig:
	rules: List[GradeRule]
	min_dscr_hard: float = 1.10
	max_ltv_hard: float = 0.85
	version: str = "default"

	@staticmethod
	def default() -> "GradingConfig":
		return GradingConfig(
			rules=[
				GradeRule("A", max_pd=0.010, min_dscr=1.50, max_ltv=0.60),
				GradeRule("B", max_pd=0.025, min_dscr=1.35, max_ltv=0.70),
				GradeRule("C", max_pd=0.050, min_dscr=1.20, max_ltv=0.80),
				GradeRule("D", max_pd=0.100, min_dscr=1.10, max_ltv=0.85),
			],
			min_dscr_hard=1.10,
			max_ltv_hard=0.85,
			version="default",
		)


def _load_config() -> GradingConfig:
	path = Path(__file__).resolve().parents[1] / "config" / "grading.yaml"
	if path.exists():
		data = yaml.safe_load(path.read_text())
		rules = [GradeRule(**r) for r in data.get("rules", [])]
		return GradingConfig(rules=rules, min_dscr_hard=data.get("min_dscr_hard", 1.10), max_ltv_hard=data.get("max_ltv_hard", 0.85), version=data.get("version", "custom"))
	return GradingConfig.default()


def grade_and_recommend(dscr: float, ltv: float, pd: float) -> tuple[str, str]:
	cfg = _load_config()
	for rule in cfg.rules:
		if pd <= rule.max_pd and dscr >= rule.min_dscr and ltv <= rule.max_ltv:
			rec = "Approve"
			return rule.grade, rec
	# Guardrails
	if dscr < cfg.min_dscr_hard or ltv > cfg.max_ltv_hard:
		return "E", "Decline"
	return "D", "Approve with conditions"
