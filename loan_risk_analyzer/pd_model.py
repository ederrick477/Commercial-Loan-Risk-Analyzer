from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import math
import yaml


@dataclass
class PDConfig:
	intercept: float = -3.0
	beta_dscr: float = -1.2
	beta_ltv: float = 1.5
	beta_coverage: float = -0.8
	version: str = "default"


class PDModel:
	def __init__(self, config_path: Optional[Path] = None) -> None:
		self.config = self._load_config(config_path)

	def _load_config(self, config_path: Optional[Path]) -> PDConfig:
		if config_path and config_path.exists():
			data = yaml.safe_load(config_path.read_text())
			return PDConfig(**data)
		default_path = Path(__file__).resolve().parents[1] / "config" / "pd.yaml"
		if default_path.exists():
			data = yaml.safe_load(default_path.read_text())
			return PDConfig(**data)
		return PDConfig()

	def predict(self, dscr: float, ltv: float, coverage: float) -> float:
		features = {
			"dscr": float("nan") if dscr is None else dscr,
			"ltv": float("nan") if ltv is None else ltv,
			"coverage": float("nan") if coverage is None else coverage,
		}
		for k, v in features.items():
			if math.isnan(v) or math.isinf(v):
				features[k] = 0.0
		lin = (
			self.config.intercept
			+ self.config.beta_dscr * features["dscr"]
			+ self.config.beta_ltv * features["ltv"]
			+ self.config.beta_coverage * features["coverage"]
		)
		return 1.0 / (1.0 + math.exp(-lin))
