from __future__ import annotations

import pandas as pd


def add_fib_features(
    df: pd.DataFrame,
    lookback: int = 30,
) -> pd.DataFrame:
    out = df.copy()

    recent_low = out["low"].rolling(lookback).min().shift(1)
    recent_high = out["high"].rolling(lookback).max().shift(1)

    leg_range = (recent_high - recent_low).replace(0, pd.NA)

    bullish_50 = recent_high - (leg_range * 0.500)
    bullish_618 = recent_high - (leg_range * 0.618)
    bullish_705 = recent_high - (leg_range * 0.705)

    bearish_50 = recent_low + (leg_range * 0.500)
    bearish_618 = recent_low + (leg_range * 0.618)
    bearish_705 = recent_low + (leg_range * 0.705)

    out["fib_recent_low"] = recent_low
    out["fib_recent_high"] = recent_high

    out["fib_bull_50"] = bullish_50
    out["fib_bull_618"] = bullish_618
    out["fib_bull_705"] = bullish_705

    out["fib_bear_50"] = bearish_50
    out["fib_bear_618"] = bearish_618
    out["fib_bear_705"] = bearish_705

    out["fib_bull_discount_50_618"] = (
        (out["low"] <= bullish_50)
        & (out["high"] >= bullish_618)
    )

    out["fib_bull_deep_618_705"] = (
        (out["low"] <= bullish_618)
        & (out["high"] >= bullish_705)
    )

    out["fib_bear_premium_50_618"] = (
        (out["high"] >= bearish_50)
        & (out["low"] <= bearish_618)
    )

    out["fib_bear_deep_618_705"] = (
        (out["high"] >= bearish_618)
        & (out["low"] <= bearish_705)
    )

    if "bull_fvg" in out.columns:
        out["fib_bull_fvg_confluence"] = (
            out["bull_fvg"]
            & (
                out["fib_bull_discount_50_618"]
                | out["fib_bull_deep_618_705"]
            )
        )

    if "bear_fvg" in out.columns:
        out["fib_bear_fvg_confluence"] = (
            out["bear_fvg"]
            & (
                out["fib_bear_premium_50_618"]
                | out["fib_bear_deep_618_705"]
            )
        )

    return out
