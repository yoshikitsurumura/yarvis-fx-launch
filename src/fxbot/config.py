from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any, Dict

import yaml


@dataclass
class AppConfig:
    raw: Dict[str, Any]

    @property
    def csv_path(self) -> pathlib.Path:
        p = self.raw.get("data", {}).get("csv_path")
        return pathlib.Path(p) if p else pathlib.Path("data/input.csv")

    @property
    def report_dir(self) -> pathlib.Path:
        p = self.raw.get("output", {}).get("report_dir", "out")
        return pathlib.Path(p)

    @property
    def strategy_name(self) -> str:
        return self.raw.get("strategy", {}).get("name", "momo_atr")

    @property
    def strategy_params(self) -> Dict[str, Any]:
        return self.raw.get("strategy", {}).get("params", {})

    @property
    def risk_params(self) -> Dict[str, Any]:
        return self.raw.get("risk", {})

    @property
    def backtest_params(self) -> Dict[str, Any]:
        return self.raw.get("backtest", {})

    @property
    def general(self) -> Dict[str, Any]:
        return self.raw.get("general", {})


def load_config(path: str | pathlib.Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig(raw=data or {})

