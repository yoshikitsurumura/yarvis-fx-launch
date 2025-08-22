from __future__ import annotations

import pandas as pd

def momentum_score(df: pd.DataFrame) -> pd.Series:
    """
    Example AI adapter: returns a simple momentum score [0..1].
    Replace this with your own model inference.
    """
    close = pd.to_numeric(df["close"], errors="coerce")
    fast = close.rolling(10, min_periods=1).mean()
    slow = close.rolling(30, min_periods=1).mean()
    raw = (fast - slow)
    # normalize by recent volatility to get 0..1-ish
    vol = (close.rolling(30, min_periods=1).std() + 1e-9)
    z = (raw / vol).clip(-3, 3)
    score = (z - z.min()) / (z.max() - z.min() + 1e-9)
    return score.fillna(0.5)

