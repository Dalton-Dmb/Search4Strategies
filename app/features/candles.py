from __future__ import annotations
import numpy as np
import pandas as pd

def add_candle_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["body"] = (out["close"] - out["open"]).abs()
    out["range"] = (out["high"] - out["low"]).replace(0, np.nan)
    out["upper_wick"] = out["high"] - out[["open","close"]].max(axis=1)
    out["lower_wick"] = out[["open","close"]].min(axis=1) - out["low"]
    out["body_pct"] = out["body"] / out["range"]
    out["upper_wick_pct"] = out["upper_wick"] / out["range"]
    out["lower_wick_pct"] = out["lower_wick"] / out["range"]
    out["direction"] = np.where(out["close"] > out["open"], 1, np.where(out["close"] < out["open"], -1, 0))
    out["engulf_bull"] = ((out["direction"] == 1) & (out["open"] <= out["close"].shift(1)) & (out["close"] >= out["open"].shift(1))).astype(int)
    out["engulf_bear"] = ((out["direction"] == -1) & (out["open"] >= out["close"].shift(1)) & (out["close"] <= out["open"].shift(1))).astype(int)
    out["large_body"] = (out["body"] > out["body"].rolling(50, min_periods=10).median() * 1.8).astype(int)
    out["rejection_bull"] = ((out["lower_wick_pct"] > 0.55) & (out["close"] > out["open"])).astype(int)
    out["rejection_bear"] = ((out["upper_wick_pct"] > 0.55) & (out["close"] < out["open"])).astype(int)
    return out.fillna(0)

