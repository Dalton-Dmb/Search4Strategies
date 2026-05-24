from __future__ import annotations

import pandas as pd


def add_ichimoku_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    high_9 = out["high"].rolling(9).max()
    low_9 = out["low"].rolling(9).min()
    out["tenkan"] = (high_9 + low_9) / 2

    high_26 = out["high"].rolling(26).max()
    low_26 = out["low"].rolling(26).min()
    out["kijun"] = (high_26 + low_26) / 2

    out["senkou_a"] = ((out["tenkan"] + out["kijun"]) / 2).shift(26)

    high_52 = out["high"].rolling(52).max()
    low_52 = out["low"].rolling(52).min()
    out["senkou_b"] = ((high_52 + low_52) / 2).shift(26)

    cloud_top = out[["senkou_a", "senkou_b"]].max(axis=1)
    cloud_bottom = out[["senkou_a", "senkou_b"]].min(axis=1)

    out["price_above_cloud"] = out["close"] > cloud_top
    out["price_below_cloud"] = out["close"] < cloud_bottom
    out["tenkan_above_kijun"] = out["tenkan"] > out["kijun"]
    out["tenkan_below_kijun"] = out["tenkan"] < out["kijun"]

    out["ichimoku_bull"] = (
        out["price_above_cloud"]
        & out["tenkan_above_kijun"]
        & (out["senkou_a"] > out["senkou_b"])
    )

    out["ichimoku_bear"] = (
        out["price_below_cloud"]
        & out["tenkan_below_kijun"]
        & (out["senkou_a"] < out["senkou_b"])
    )

    return out
