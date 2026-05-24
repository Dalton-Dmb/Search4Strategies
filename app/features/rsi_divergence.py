from __future__ import annotations

import pandas as pd


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def add_rsi_divergence_features(
    df: pd.DataFrame,
    period: int = 14,
    lookback: int = 10,
) -> pd.DataFrame:
    out = df.copy()

    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out["high"] = pd.to_numeric(out["high"], errors="coerce")
    out["low"] = pd.to_numeric(out["low"], errors="coerce")

    out["rsi"] = _rsi(out["close"], period)
    out["rsi"] = pd.to_numeric(out["rsi"], errors="coerce")

    prior_low = out["low"].rolling(lookback, min_periods=lookback).min().shift(1)
    prior_high = out["high"].rolling(lookback, min_periods=lookback).max().shift(1)

    prior_rsi_low = out["rsi"].rolling(lookback, min_periods=lookback).min().shift(1)
    prior_rsi_high = out["rsi"].rolling(lookback, min_periods=lookback).max().shift(1)

    out["rsi_bull_div"] = (
        (out["low"] < prior_low)
        & (out["rsi"] > prior_rsi_low)
        & (out["rsi"] < 45)
    ).fillna(False)

    out["rsi_bear_div"] = (
        (out["high"] > prior_high)
        & (out["rsi"] < prior_rsi_high)
        & (out["rsi"] > 55)
    ).fillna(False)

    out["rsi_bull_regime"] = (out["rsi"] > 55).fillna(False)
    out["rsi_strong_bull_regime"] = (out["rsi"] > 60).fillna(False)
    out["rsi_bear_regime"] = (out["rsi"] < 45).fillna(False)
    out["rsi_chop_zone"] = (
        (out["rsi"] >= 45)
        & (out["rsi"] <= 55)
    ).fillna(False)
    
    return out
