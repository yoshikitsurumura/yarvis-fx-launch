from __future__ import annotations

import pandas as pd
from typing import Iterable


def load_events_csv(path: str) -> pd.DatetimeIndex:
    """Load events CSV with at least 'timestamp' column.
    The timestamp is parsed as UTC-aware.
    """
    df = pd.read_csv(path)
    if "timestamp" not in {c.lower() for c in df.columns}:
        raise ValueError("events CSV must include a 'timestamp' column")
    # normalize column name
    col_map = {c: c.lower() for c in df.columns}
    df = df.rename(columns=col_map)
    idx = pd.to_datetime(df["timestamp"], utc=True)
    return pd.DatetimeIndex(idx)


def build_blackout_mask(index: pd.DatetimeIndex, events: Iterable[pd.Timestamp], *, before_min: int, after_min: int) -> pd.Series:
    """Return boolean Series indexed by index: True if entry allowed, False if blacked out.

    Blackout window: [event - before_min, event + after_min]
    """
    mask = pd.Series(True, index=index)
    if not events:
        return mask
    # Create intervals and mark
    for ev in events:
        start = ev - pd.Timedelta(minutes=int(before_min))
        end = ev + pd.Timedelta(minutes=int(after_min))
        mask[(mask.index >= start) & (mask.index <= end)] = False
    return mask

