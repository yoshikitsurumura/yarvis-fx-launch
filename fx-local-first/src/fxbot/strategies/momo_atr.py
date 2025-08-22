from __future__ import annotations

import pandas as pd

from ..indicators import ema, atr


def generate_signals(df: pd.DataFrame, *, ema_fast: int, ema_slow: int, atr_window: int,
                     vol_filter_min_atr_pct: float = 0.0) -> pd.DataFrame:
    """
    Returns DataFrame with columns: close, ema_fast, ema_slow, atr, signal
    signal: 1 for long, 0 for flat
    """
    out = df.copy()
    out["ema_fast"] = ema(out["close"], ema_fast)
    out["ema_slow"] = ema(out["close"], ema_slow)
    out["atr"] = atr(out["high"], out["low"], out["close"], window=atr_window)
    out["rel_atr"] = out["atr"] / out["close"].replace(0, pd.NA)
    # momentum condition
    mom = (out["ema_fast"] > out["ema_slow"]).astype(int)
    # volatility filter
    if vol_filter_min_atr_pct and vol_filter_min_atr_pct > 0:
        vol_ok = (out["rel_atr"] >= vol_filter_min_atr_pct)
        sig = (mom & vol_ok).astype(int)
    else:
        sig = mom
    out["signal"] = sig
    return out.dropna()

