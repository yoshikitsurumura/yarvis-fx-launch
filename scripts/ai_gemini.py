from __future__ import annotations

"""
Gemini adapter for the Web UI AI bridge.

Usage (Windows PowerShell):
- pip install google-generativeai
- $env:GEMINI_API_KEY = "..."
- In Web UI AI field: scripts.ai_gemini:gemini_score

Notes:
- This is best used as a coarse advisor or daily risk flag, not per-tick.
- If library or API key is missing, falls back to a simple momentum score.
"""

import os
from typing import Iterable
import pandas as pd


def _fallback_score(df: pd.DataFrame) -> pd.Series:
    close = pd.to_numeric(df["close"], errors="coerce")
    fast = close.rolling(10, min_periods=1).mean()
    slow = close.rolling(30, min_periods=1).mean()
    raw = (fast - slow)
    vol = (close.rolling(30, min_periods=1).std() + 1e-9)
    z = (raw / vol).clip(-3, 3)
    score = (z - z.min()) / (z.max() - z.min() + 1e-9)
    return score.fillna(0.5)


def _format_series_for_prompt(df: pd.DataFrame, tail: int = 128) -> str:
    s = df.tail(tail)
    # Compact CSV lines: ts, o, h, l, c
    lines: list[str] = ["timestamp,open,high,low,close"]
    for ts, row in s.iterrows():
        lines.append(f"{ts.isoformat()},{row['open']:.5f},{row['high']:.5f},{row['low']:.5f},{row['close']:.5f}")
    return "\n".join(lines)


def gemini_score(df: pd.DataFrame, *, model: str = "gemini-1.5-flash", tail: int = 128) -> pd.Series:
    """
    Return a per-row score Series (0..1). For practicality, we:
    - Ask Gemini for a single probability for the latest bar given last N bars.
    - Fill previous bars with a rolling fallback score to keep the same index length.
    """
    # Hard safety gate: require explicit allowance
    if os.environ.get("FXBOT_ALLOW_ONLINE", "0") not in ("1", "true", "TRUE", "True"):
        return _fallback_score(df)

    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        return _fallback_score(df)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _fallback_score(df)

    genai.configure(api_key=api_key)
    prompt = (
        "You are a quantitative assistant. Given recent OHLC data, estimate the probability "
        "that the next-bar close will be higher than the last close. Respond ONLY with a JSON object, "
        "like {\"prob_up\": 0.63}.\n\n" + _format_series_for_prompt(df, tail=tail)
    )

    prob = 0.5
    try:
        model_obj = genai.GenerativeModel(model)
        resp = model_obj.generate_content(prompt)
        text = (resp.text or "").strip()
        # naive parse
        import json
        j = json.loads(text) if text.startswith("{") else {}
        prob = float(j.get("prob_up", 0.5))
        if not (0.0 <= prob <= 1.0):
            prob = 0.5
    except Exception:
        prob = 0.5

    base = _fallback_score(df)
    # Blend towards Gemini prob at the last index
    s = base.copy()
    if len(s) > 0:
        s.iloc[-1] = prob
    return s
