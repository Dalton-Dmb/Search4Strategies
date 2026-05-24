from __future__ import annotations
from app.execution.execution_profiles import get_execution_profile
from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class TradeSignal:
    symbol: str
    timeframe: str
    side: str
    rule: str
    entry: float
    stop_loss: float
    take_profit: float
    risk_r: float
    reward_r: float
    candle_index: int
    valid: bool
    reason: str


def _rule_matches(row: pd.Series, rule: str) -> bool:
    parts = [p.strip() for p in rule.split("AND")]

    for part in parts:
        if part not in row.index:
            return False

        if not bool(row[part]):
            return False

    return True


def _recent_swing_low(df: pd.DataFrame, idx: int, lookback: int = 10) -> float:
    start = max(0, idx - lookback)
    return float(df.iloc[start:idx + 1]["low"].min())


def _recent_swing_high(df: pd.DataFrame, idx: int, lookback: int = 10) -> float:
    start = max(0, idx - lookback)
    return float(df.iloc[start:idx + 1]["high"].max())


def _bullish_fvg_midpoint(df: pd.DataFrame, idx: int) -> Optional[float]:
    if idx < 2:
        return None

    candle_1_high = float(df.iloc[idx - 2]["high"])
    candle_3_low = float(df.iloc[idx]["low"])

    if candle_3_low > candle_1_high:
        return (candle_1_high + candle_3_low) / 2.0

    return None


def _bearish_fvg_midpoint(df: pd.DataFrame, idx: int) -> Optional[float]:
    if idx < 2:
        return None

    candle_1_low = float(df.iloc[idx - 2]["low"])
    candle_3_high = float(df.iloc[idx]["high"])

    if candle_3_high < candle_1_low:
        return (candle_1_low + candle_3_high) / 2.0

    return None


def generate_signal(
    features: pd.DataFrame,
    symbol: str,
    timeframe: str,
    rule: str,
    side: str,
    target_r: float = 5.0,
    risk_buffer_atr: float = 0.25,
    swing_lookback: int = 10,
    use_fvg_entry: bool = True,
) -> Optional[TradeSignal]:
    if features.empty:
        return None

    df = features.reset_index(drop=True).copy()
    idx = len(df) - 1
    row = df.iloc[idx]

    if not _rule_matches(row, rule):
        return TradeSignal(
            symbol=symbol,
            timeframe=timeframe,
            side=side,
            rule=rule,
            entry=float(row["close"]),
            stop_loss=0.0,
            take_profit=0.0,
            risk_r=0.0,
            reward_r=0.0,
            candle_index=idx,
            valid=False,
            reason="Rule conditions not met on latest candle.",
        )

    entry = float(row["close"])
    reason = "Rule conditions met. Signal generated."

    if use_fvg_entry and side == "long" and "bull_fvg" in rule:
        fvg_entry = _bullish_fvg_midpoint(df, idx)
        if fvg_entry is not None:
            entry = float(fvg_entry)
            reason = "Rule met. Bullish FVG midpoint retracement entry generated."

    if use_fvg_entry and side == "short" and "bear_fvg" in rule:
        fvg_entry = _bearish_fvg_midpoint(df, idx)
        if fvg_entry is not None:
            entry = float(fvg_entry)
            reason = "Rule met. Bearish FVG midpoint retracement entry generated."

    profile = get_execution_profile(symbol)

    atr = float(row.get("atr", 0.0) or 0.0)
    atr_stop_mult = float(profile.get("atr_stop_mult", 1.0))

    buffer = atr * atr_stop_mult

    if side == "long":
        swing_low = _recent_swing_low(df, idx, swing_lookback)
        stop_loss = swing_low - buffer
        risk = entry - stop_loss

        if risk <= 0:
            return TradeSignal(
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                rule=rule,
                entry=entry,
                stop_loss=stop_loss,
                take_profit=0.0,
                risk_r=0.0,
                reward_r=0.0,
                candle_index=idx,
                valid=False,
                reason="Invalid long risk calculation.",
            )

        take_profit = entry + (risk * target_r)

    elif side == "short":
        swing_high = _recent_swing_high(df, idx, swing_lookback)
        stop_loss = swing_high + buffer
        risk = stop_loss - entry

        if risk <= 0:
            return TradeSignal(
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                rule=rule,
                entry=entry,
                stop_loss=stop_loss,
                take_profit=0.0,
                risk_r=0.0,
                reward_r=0.0,
                candle_index=idx,
                valid=False,
                reason="Invalid short risk calculation.",
            )

        take_profit = entry - (risk * target_r)

    else:
        return TradeSignal(
            symbol=symbol,
            timeframe=timeframe,
            side=side,
            rule=rule,
            entry=entry,
            stop_loss=0.0,
            take_profit=0.0,
            risk_r=0.0,
            reward_r=0.0,
            candle_index=idx,
            valid=False,
            reason=f"Unsupported side: {side}",
        )

    return TradeSignal(
        symbol=symbol,
        timeframe=timeframe,
        side=side,
        rule=rule,
        entry=float(entry),
        stop_loss=float(stop_loss),
        take_profit=float(take_profit),
        risk_r=1.0,
        reward_r=float(target_r),
        candle_index=idx,
        valid=True,
        reason=reason,
    )
