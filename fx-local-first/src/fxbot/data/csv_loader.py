from __future__ import annotations

import pandas as pd


def load_ohlcv_csv(path: str | bytes | "os.PathLike[str]") -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize columns
    cols = {c.lower(): c for c in df.columns}
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in cols]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")
    # Ensure correct dtypes
    df = df.rename(columns={cols[c]: c for c in required})
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    num_cols = ["open", "high", "low", "close", "volume"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().sort_values("timestamp")
    df = df.set_index("timestamp")
    return df

