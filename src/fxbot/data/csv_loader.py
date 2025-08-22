from __future__ import annotations

from typing import Dict, Mapping, Optional
import pandas as pd


def load_ohlcv_csv(
    path: str | bytes | "os.PathLike[str]",
    *,
    column_map: Optional[Mapping[str, str]] = None,
) -> pd.DataFrame:
    """
    Load OHLCV CSV with flexible column names.
    - Accepts typical variants for timestamp: timestamp/date/datetime/time.
    - 'volume' is optional; if missing, fills with zeros.
    - 'column_map' can be provided to explicitly map logical names -> actual column names.
    """
    df = pd.read_csv(path)
    # Normalize lookup by lowercase
    lower_map = {c.lower(): c for c in df.columns}

    # Build desired mapping
    want = {
        "timestamp": None,
        "open": None,
        "high": None,
        "low": None,
        "close": None,
        "volume": None,
    }  # type: Dict[str, Optional[str]]

    # Apply explicit mapping if provided
    if column_map:
        for k, v in column_map.items():
            if k in want and v in df.columns:
                want[k] = v

    # Infer timestamp if not provided
    if want["timestamp"] is None:
        for cand in ("timestamp", "time", "date", "datetime"):
            if cand in lower_map:
                want["timestamp"] = lower_map[cand]
                break

    # Infer OHLC if not provided (common exact names cover most cases)
    for k in ("open", "high", "low", "close", "volume"):
        if want[k] is None and k in lower_map:
            want[k] = lower_map[k]

    # Validate minimal required columns (OHLC and timestamp)
    missing_min = [k for k in ("timestamp", "open", "high", "low", "close") if not want[k]]
    if missing_min:
        raise ValueError(f"CSV missing columns: {missing_min}")

    # Rename to canonical names
    rename_map = {want[k]: k for k in want if want[k] is not None}
    df = df.rename(columns=rename_map)

    # Parse timestamp and numeric
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    # Volume: optional -> fill 0 if missing
    if "volume" not in df.columns:
        df["volume"] = 0.0
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp")
    df = df.set_index("timestamp")
    return df
