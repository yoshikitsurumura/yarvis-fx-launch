from __future__ import annotations

from importlib import import_module
from typing import Callable
import pandas as pd


def _load_callable(path: str) -> Callable[[pd.DataFrame], pd.Series]:
    """
    Load a Python callable specified as 'module.sub:func'.
    The callable must accept a DataFrame and return a Series/array-like scores.
    """
    if ":" not in path:
        raise ValueError("callable path must be like 'package.mod:function'")
    mod_path, func_name = path.split(":", 1)
    mod = import_module(mod_path)
    fn = getattr(mod, func_name)
    if not callable(fn):
        raise TypeError(f"{path} is not callable")
    return fn  # type: ignore[return-value]


def generate_signals_from_callable(
    df: pd.DataFrame,
    *,
    callable_path: str,
    threshold: float = 0.5,
) -> pd.DataFrame:
    """
    Use a user-provided callable to produce long/flat signals.
    The callable must return a score per row (0..1 or any real), thresholded to 1/0.
    """
    fn = _load_callable(callable_path)
    scores = fn(df)
    s = pd.Series(scores, index=df.index)
    sig = (s >= threshold).astype(int)
    out = df.copy()
    out["signal"] = sig
    # Ensure required columns exist for backtest pipeline
    needed = ["open", "high", "low", "close"]
    for c in needed:
        if c not in out.columns:
            raise ValueError(f"input DataFrame missing required column: {c}")
    # Create dummy ATR if absent (no ATR stop when missing)
    if "atr" not in out.columns:
        out["atr"] = (out["high"] - out["low"]).rolling(14, min_periods=1).mean()
    return out

