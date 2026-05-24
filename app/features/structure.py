from __future__ import annotations
import numpy as np
import pandas as pd

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high-low), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=period).mean().bfill()

def add_structure_features(df: pd.DataFrame, swing: int = 5) -> pd.DataFrame:
    out = df.copy()
    out["atr"] = atr(out)
    out["volatility_rel"] = out["atr"] / out["close"]
    out["rolling_high"] = out["high"].rolling(swing*2+1, center=True).max()
    out["rolling_low"] = out["low"].rolling(swing*2+1, center=True).min()
    out["swing_high"] = (out["high"] == out["rolling_high"]).astype(int)
    out["swing_low"] = (out["low"] == out["rolling_low"]).astype(int)
    out["prev_high_20"] = out["high"].rolling(20).max().shift(1)
    out["prev_low_20"] = out["low"].rolling(20).min().shift(1)
    out["sweep_high"] = ((out["high"] > out["prev_high_20"]) & (out["close"] < out["prev_high_20"])).astype(int)
    out["sweep_low"] = ((out["low"] < out["prev_low_20"]) & (out["close"] > out["prev_low_20"])).astype(int)
    out["bull_fvg"] = (out["low"] > out["high"].shift(2)).astype(int)
    out["bear_fvg"] = (out["high"] < out["low"].shift(2)).astype(int)
    out["session_hour"] = pd.to_datetime(out["time"]).dt.hour
    out["dow"] = pd.to_datetime(out["time"]).dt.dayofweek
    out["london"] = out["session_hour"].between(7, 11).astype(int)
    out["ny"] = out["session_hour"].between(13, 17).astype(int)
    out["overlap"] = out["session_hour"].between(13, 16).astype(int)
    return out.drop(columns=["rolling_high","rolling_low"], errors="ignore").fillna(0)

