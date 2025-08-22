from __future__ import annotations

import pathlib
from typing import Optional

import pandas as pd
import yfinance as yf


def pair_to_yahoo_symbol(pair: str) -> str:
    p = pair.strip().upper().replace("/", "")
    if p.endswith("=X"):
        return p
    if len(p) == 6:
        return f"{p}=X"
    # Accept tickers like XAUUSD
    if len(p) == 6 and p.endswith("USD"):
        return f"{p}=X"
    return p


def fetch_ohlcv_yahoo(
    pair: str,
    *,
    interval: str = "1h",
    period: Optional[str] = "2y",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch OHLCV from Yahoo Finance and return normalized DataFrame.

    interval examples: 1m, 5m, 15m, 1h, 1d
    period examples: 7d, 60d, 1y, 2y. If start is provided, period is ignored.
    """
    symbol = pair_to_yahoo_symbol(pair)
    kwargs = {"tickers": symbol, "interval": interval, "auto_adjust": False}
    if start:
        kwargs.update({"start": start, "end": end})
    else:
        kwargs.update({"period": period or "1y"})

    df = yf.download(**kwargs)
    if df is None or len(df) == 0:
        raise RuntimeError(f"No data returned from Yahoo for {symbol} ({pair})")
    # When multi-index columns returned, pick first level
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)
    # Normalize columns
    cols = {c.lower(): c for c in df.columns}
    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in cols]
    if missing:
        # Some intervals may return missing Volume; fill with zeros
        for m in missing:
            if m == "volume":
                df["Volume"] = 0
            else:
                raise RuntimeError(f"Yahoo columns missing: {missing}")
    out = df.rename(columns={
        cols.get("open", "Open"): "open",
        cols.get("high", "High"): "high",
        cols.get("low", "Low"): "low",
        cols.get("close", "Close"): "close",
        cols.get("volume", "Volume"): "volume",
    })
    # Ensure timezone-aware UTC index
    idx = pd.to_datetime(out.index, utc=True)
    out = out.set_index(idx)
    out.index.name = "timestamp"
    out = out[["open", "high", "low", "close", "volume"]].dropna()
    return out


def save_df_to_csv(df: pd.DataFrame, path: str | pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index().to_csv(path, index=False)
    return path

