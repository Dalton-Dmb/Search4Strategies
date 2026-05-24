from __future__ import annotations

import pandas as pd


def add_fib_features(
    df: pd.DataFrame,
    lookback: int = 30,
) -> pd.DataFrame:
    out = df.copy()

    out["high"] = pd.to_numeric(out["high"], errors="coerce")
    out["low"] = pd.to_numeric(out["low"], errors="coerce")

    recent_low = out["low"].rolling(
        lookback,
        min_periods=lookback,
    ).min().shift(1)

    recent_high = out["high"].rolling(
        lookback,
        min_periods=lookback,
    ).max().shift(1)

    leg_range = recent_high - recent_low
    leg_range = leg_range.where(leg_range != 0)

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
        (out["low"].le(bullish_50))
        & (out["high"].ge(bullish_618))
    ).fillna(False)

    out["fib_bull_deep_618_705"] = (
        (out["low"].le(bullish_618))
        & (out["high"].ge(bullish_705))
    ).fillna(False)

    out["fib_bear_premium_50_618"] = (
        (out["high"].ge(bearish_50))
        & (out["low"].le(bearish_618))
    ).fillna(False)

    out["fib_bear_deep_618_705"] = (
        (out["high"].ge(bearish_618))
        & (out["low"].le(bearish_705))
    ).fillna(False)

    if "bull_fvg" in out.columns:
        out["fib_bull_fvg_confluence"] = (
            out["bull_fvg"].fillna(False).astype(bool)
            & (
                out["fib_bull_discount_50_618"]
                | out["fib_bull_deep_618_705"]
            )
        )

    if "bear_fvg" in out.columns:
        out["fib_bear_fvg_confluence"] = (
            out["bear_fvg"].fillna(False).astype(bool)
            & (
                out["fib_bear_premium_50_618"]
                | out["fib_bear_deep_618_705"]
            )
        )

    return out
