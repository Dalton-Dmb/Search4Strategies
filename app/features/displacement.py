from __future__ import annotations

import pandas as pd


def add_displacement_features(df: pd.DataFrame, atr_period: int = 14) -> pd.DataFrame:
    out = df.copy()

    prev_close = out["close"].shift(1)

    tr1 = out["high"] - out["low"]
    tr2 = (out["high"] - prev_close).abs()
    tr3 = (out["low"] - prev_close).abs()

    out["true_range"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    out["atr"] = out["true_range"].rolling(atr_period).mean()

    body = (out["close"] - out["open"]).abs()
    candle_range = (out["high"] - out["low"]).replace(0, pd.NA)

    out["body_ratio"] = body / candle_range
    out["atr_expansion"] = out["true_range"] > (out["atr"] * 1.25)

    out["bull_displacement"] = (
        (out["close"] > out["open"])
        & (out["body_ratio"] >= 0.60)
        & out["atr_expansion"]
    )

    out["bear_displacement"] = (
        (out["close"] < out["open"])
        & (out["body_ratio"] >= 0.60)
        & out["atr_expansion"]
    )

    return out
