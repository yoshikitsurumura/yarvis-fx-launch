from __future__ import annotations

import pathlib
from typing import Optional

import pandas as pd


# Stooq provides daily data reliably; intraday availability varies.
# Ticker format examples: USDJPY for FX, XAUUSD for Gold/USD.


def fetch_ohlcv_stooq(pair: str, *, timeframe: str = "1d") -> pd.DataFrame:
    """Fetch daily OHLC from Stooq. Intraday is not guaranteed.

    Note: This uses a public CSV endpoint; please respect usage terms.
    """
    sym = pair.strip().upper().replace("/", "")
    # Daily CSV URL pattern (may change; treat as best-effort)
    url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
    df = pd.read_csv(url)
    df = df.rename(columns={
        "Date": "timestamp",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    })
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().sort_values("timestamp").set_index("timestamp")
    return df[["open", "high", "low", "close", "volume"]]


def save_df_to_csv(df: pd.DataFrame, path: str | pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index().to_csv(path, index=False)
    return path

