from __future__ import annotations

import os
import pathlib
from typing import Optional

import pandas as pd
import requests


def _fx_function_for_interval(interval: str) -> str:
    interval = interval.lower()
    if interval.endswith("m"):
        return "FX_INTRADAY"
    if interval.endswith("h"):
        return "FX_INTRADAY"
    # daily
    return "FX_DAILY"


def _normalize_interval(interval: str) -> str:
    m = interval.lower()
    # Alpha Vantage supports 1min,5min,15min,30min,60min
    if m in {"1m", "5m", "15m", "30m", "60m", "1min", "5min", "15min", "30min", "60min"}:
        return {"1m":"1min","5m":"5min","15m":"15min","30m":"30min","60m":"60min",
                "1min":"1min","5min":"5min","15min":"15min","30min":"30min","60min":"60min"}[m]
    if m in {"1h"}:
        return "60min"
    return "daily"


def fetch_ohlcv_alphavantage(pair: str, *, interval: str = "1h", api_key: Optional[str] = None) -> pd.DataFrame:
    """Fetch FX OHLC from Alpha Vantage (free tier). Volume is not provided and will be 0.

    Note: Requires API key (free). Set env ALPHAVANTAGE_API_KEY or pass api_key.
    """
    api_key = api_key or os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("Alpha Vantage API key not set. Set ALPHAVANTAGE_API_KEY.")

    base = "https://www.alphavantage.co/query"
    p = pair.strip().upper().replace("/", "")
    if len(p) != 6:
        raise ValueError("Pair must be like USDJPY/EURUSD")
    from_symbol, to_symbol = p[:3], p[3:]

    func = _fx_function_for_interval(interval)
    norm_int = _normalize_interval(interval)

    params = {
        "function": func,
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "apikey": api_key,
    }
    if func == "FX_INTRADAY":
        params["interval"] = norm_int
        params["outputsize"] = "full"

    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Handle API errors or rate limits
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected Alpha Vantage response")
    if "Error Message" in data:
        raise RuntimeError(f"Alpha Vantage error: {data.get('Error Message')}")
    if "Note" in data:
        # Usually rate limit notice
        raise RuntimeError(f"Alpha Vantage note: {data.get('Note')}")

    # Determine the correct timeseries key
    ts_key = None
    if func == "FX_INTRADAY":
        # Example: "Time Series FX (5min)" or "Time Series FX (60min)"
        for k in data.keys():
            if k.startswith("Time Series FX ("):
                ts_key = k
                break
    else:
        ts_key = "Time Series FX (Daily)"

    if not ts_key or ts_key not in data:
        raise RuntimeError("Alpha Vantage: time series not found in response")

    ts = data[ts_key]
    if not isinstance(ts, dict) or not ts:
        raise RuntimeError("Alpha Vantage: empty time series")

    # Build DataFrame
    df = (
        pd.DataFrame.from_dict(ts, orient="index")
        .rename(columns={
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
        })
    )
    # Index to UTC timestamps
    idx = pd.to_datetime(df.index, utc=True)
    df.index = idx
    df.index.name = "timestamp"
    # Ensure numeric
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["volume"] = 0
    out = df[["open", "high", "low", "close", "volume"]].dropna().sort_index()
    return out


def save_df_to_csv(df: pd.DataFrame, path: str | pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index().to_csv(path, index=False)
    return path

    # Determine time series key
    ts_key = next((k for k in data.keys() if "Time Series" in k), None)
    if not ts_key:
        raise RuntimeError(f"Unexpected Alpha Vantage response: {list(data.keys())[:3]}")
    ts = data[ts_key]
    df = pd.DataFrame.from_dict(ts, orient="index")
    # Columns like: 1. open, 2. high, 3. low, 4. close
    rename_map = {
        next((c for c in df.columns if "open" in c), None): "open",
        next((c for c in df.columns if "high" in c), None): "high",
        next((c for c in df.columns if "low" in c), None): "low",
        next((c for c in df.columns if "close" in c), None): "close",
    }
    df = df.rename(columns=rename_map)
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["volume"] = 0
    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "timestamp"
    df = df.sort_index()
    return df[["open", "high", "low", "close", "volume"]].dropna()


def save_df_to_csv(df: pd.DataFrame, path: str | pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index().to_csv(path, index=False)
    return path
