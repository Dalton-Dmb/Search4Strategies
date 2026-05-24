from __future__ import annotations

import pandas as pd


def swing_low(candles: pd.DataFrame, idx: int, lookback: int = 5) -> float:
    start = max(0, idx - lookback)
    return float(candles.iloc[start:idx + 1]["low"].min())


def swing_high(candles: pd.DataFrame, idx: int, lookback: int = 5) -> float:
    start = max(0, idx - lookback)
    return float(candles.iloc[start:idx + 1]["high"].max())


def atr_at(candles: pd.DataFrame, idx: int) -> float:
    if "atr" not in candles.columns:
        return 0.0

    value = candles.iloc[idx].get("atr", 0.0)

    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def manage_trade_atr_profile(
    candles: pd.DataFrame,
    signal_row: pd.Series,
    horizon: int = 120,
    partial_at_r: float = 2.0,
    partial_fraction: float = 0.50,
    breakeven_at_r: float = 2.0,
    trail_after_partial: bool = True,
    trail_lookback: int = 12,
    trail_atr_mult: float = 1.0,
) -> dict:
    idx = int(signal_row["candle_index"])
    side = str(signal_row["side"]).lower()

    entry = float(signal_row["entry"])
    initial_sl = float(signal_row["stop_loss"])
    final_tp = float(signal_row["take_profit"])
    reward_r = float(signal_row["reward_r"])

    if side == "long":
        one_r = entry - initial_sl
        partial_tp = entry + (one_r * partial_at_r)
        breakeven_trigger = entry + (one_r * breakeven_at_r)
    else:
        one_r = initial_sl - entry
        partial_tp = entry - (one_r * partial_at_r)
        breakeven_trigger = entry - (one_r * breakeven_at_r)

    if one_r <= 0:
        return {
            **signal_row.to_dict(),
            "exit_index": idx,
            "outcome": "invalid_risk",
            "r_result": 0.0,
            "management": "atr_profile",
        }

    active_sl = initial_sl
    partial_taken = False
    breakeven_done = False
    trail_active = False

    realized_r = 0.0
    remaining_fraction = 1.0

    max_favorable_r = 0.0
    max_adverse_r = 0.0

    end = min(len(candles), idx + horizon + 1)

    for i in range(idx + 1, end):
        high = float(candles.iloc[i]["high"])
        low = float(candles.iloc[i]["low"])
        atr = atr_at(candles, i)

        if side == "long":
            favorable_r = (high - entry) / one_r
            adverse_r = (entry - low) / one_r

            max_favorable_r = max(max_favorable_r, favorable_r)
            max_adverse_r = max(max_adverse_r, adverse_r)

            if not breakeven_done and high >= breakeven_trigger:
                active_sl = max(active_sl, entry)
                breakeven_done = True

            if not partial_taken and high >= partial_tp:
                realized_r += partial_fraction * partial_at_r
                remaining_fraction -= partial_fraction
                partial_taken = True

            if trail_after_partial and partial_taken:
                trail_active = True
                proposed_sl = swing_low(candles, i, trail_lookback) - (atr * trail_atr_mult)
                active_sl = max(active_sl, proposed_sl)

            hit_tp = high >= final_tp
            hit_sl = low <= active_sl

            if hit_tp and hit_sl:
                runner_r = 0.0 if active_sl >= entry else -1.0
                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": "ambiguous_both_hit",
                    "r_result": realized_r + (remaining_fraction * runner_r),
                    "management": "atr_profile",
                    "partial_taken": partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

            if hit_tp:
                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": "win",
                    "r_result": realized_r + (remaining_fraction * reward_r),
                    "management": "atr_profile",
                    "partial_taken": partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

            if hit_sl:
                if active_sl >= entry:
                    outcome = "breakeven_stop"
                    runner_r = 0.0
                else:
                    outcome = "loss"
                    runner_r = -1.0

                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": outcome,
                    "r_result": realized_r + (remaining_fraction * runner_r),
                    "management": "atr_profile",
                    "partial_taken": partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

        elif side == "short":
            favorable_r = (entry - low) / one_r
            adverse_r = (high - entry) / one_r

            max_favorable_r = max(max_favorable_r, favorable_r)
            max_adverse_r = max(max_adverse_r, adverse_r)

            if not breakeven_done and low <= breakeven_trigger:
                active_sl = min(active_sl, entry)
                breakeven_done = True

            if not partial_taken and low <= partial_tp:
                realized_r += partial_fraction * partial_at_r
                remaining_fraction -= partial_fraction
                partial_taken = True

            if trail_after_partial and partial_taken:
                trail_active = True
                proposed_sl = swing_high(candles, i, trail_lookback) + (atr * trail_atr_mult)
                active_sl = min(active_sl, proposed_sl)

            hit_tp = low <= final_tp
            hit_sl = high >= active_sl

            if hit_tp and hit_sl:
                runner_r = 0.0 if active_sl <= entry else -1.0
                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": "ambiguous_both_hit",
                    "r_result": realized_r + (remaining_fraction * runner_r),
                    "management": "atr_profile",
                    "partial_taken": partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

            if hit_tp:
                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": "win",
                    "r_result": realized_r + (remaining_fraction * reward_r),
                    "management": "atr_profile",
                    "partial_taken": partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

            if hit_sl:
                if active_sl <= entry:
                    outcome = "breakeven_stop"
                    runner_r = 0.0
                else:
                    outcome = "loss"
                    runner_r = -1.0

                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": outcome,
                    "r_result": realized_r + (remaining_fraction * runner_r),
                    "management": "atr_profile",
                    "partial_taken": partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

    return {
        **signal_row.to_dict(),
        "exit_index": end - 1,
        "outcome": "timeout",
        "r_result": realized_r,
        "management": "atr_profile",
        "partial_taken": partial_taken,
        "breakeven_done": breakeven_done,
        "trail_active": trail_active,
        "active_sl": active_sl,
        "mfe_r": max_favorable_r,
        "mae_r": max_adverse_r,
    }


def manage_trade_runner_profile(
    candles: pd.DataFrame,
    signal_row: pd.Series,
    horizon: int = 240,
    partial_at_r: float = 2.0,
    partial_fraction: float = 0.50,
    breakeven_at_r: float = 1.5,
    trail_lookback: int = 8,
    trail_atr_mult: float = 0.50,
) -> dict:
    idx = int(signal_row["candle_index"])
    side = str(signal_row["side"]).lower()

    entry = float(signal_row["entry"])
    initial_sl = float(signal_row["stop_loss"])

    one_r = abs(entry - initial_sl)

    if one_r <= 0:
        return {
            **signal_row.to_dict(),
            "exit_index": idx,
            "outcome": "invalid_risk",
            "r_result": 0.0,
            "management": "runner_profile",
        }

    active_sl = initial_sl

    partial_taken = False
    breakeven_done = False
    trail_active = False

    realized_r = 0.0
    remaining_fraction = 1.0

    max_favorable_r = 0.0
    max_adverse_r = 0.0

    end = min(len(candles), idx + horizon + 1)

    for i in range(idx + 1, end):
        high = float(candles.iloc[i]["high"])
        low = float(candles.iloc[i]["low"])

        atr = atr_at(candles, i)

        if side == "long":

            favorable_r = (high - entry) / one_r
            adverse_r = (entry - low) / one_r

            max_favorable_r = max(max_favorable_r, favorable_r)
            max_adverse_r = max(max_adverse_r, adverse_r)

            breakeven_trigger = entry + (one_r * breakeven_at_r)
            partial_tp = entry + (one_r * partial_at_r)

            if not breakeven_done and high >= breakeven_trigger:
                active_sl = max(active_sl, entry)
                breakeven_done = True

            if not partial_taken and high >= partial_tp:
                realized_r += partial_fraction * partial_at_r
                remaining_fraction -= partial_fraction
                partial_taken = True

            if favorable_r >= 4.0:
                trail_active = True

            if trail_active:
                proposed_sl = (
                    swing_low(candles, i, trail_lookback)
                    - (atr * trail_atr_mult)
                )

                active_sl = max(active_sl, proposed_sl)

            if low <= active_sl:

                if active_sl >= entry:
                    runner_r = (active_sl - entry) / one_r
                    outcome = "runner_exit_profit"
                else:
                    runner_r = -1.0
                    outcome = "loss"

                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": outcome,
                    "r_result": realized_r + (remaining_fraction * runner_r),
                    "management": "runner_profile",
                    "partial_taken": partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

        elif side == "short":

            favorable_r = (entry - low) / one_r
            adverse_r = (high - entry) / one_r

            max_favorable_r = max(max_favorable_r, favorable_r)
            max_adverse_r = max(max_adverse_r, adverse_r)

            breakeven_trigger = entry - (one_r * breakeven_at_r)
            partial_tp = entry - (one_r * partial_at_r)

            if not breakeven_done and low <= breakeven_trigger:
                active_sl = min(active_sl, entry)
                breakeven_done = True

            if not partial_taken and low <= partial_tp:
                realized_r += partial_fraction * partial_at_r
                remaining_fraction -= partial_fraction
                partial_taken = True
                trail_active = True

            if trail_active:
                proposed_sl = (
                    swing_high(candles, i, trail_lookback)
                    + (atr * trail_atr_mult)
                )

                active_sl = min(active_sl, proposed_sl)

            if high >= active_sl:

                if active_sl <= entry:
                    runner_r = (entry - active_sl) / one_r
                    outcome = "runner_exit_profit"
                else:
                    runner_r = -1.0
                    outcome = "loss"

                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": outcome,
                    "r_result": realized_r + (remaining_fraction * runner_r),
                    "management": "runner_profile",
                    "partial_taken": partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

    final_close = float(candles.iloc[end - 1]["close"])

    if side == "long":
        runner_r = (final_close - entry) / one_r
    else:
        runner_r = (entry - final_close) / one_r

    return {
        **signal_row.to_dict(),
        "exit_index": end - 1,
        "outcome": "timeout_runner",
        "r_result": realized_r + (remaining_fraction * runner_r),
        "management": "runner_profile",
        "partial_taken": partial_taken,
        "breakeven_done": breakeven_done,
        "trail_active": trail_active,
        "active_sl": active_sl,
        "mfe_r": max_favorable_r,
        "mae_r": max_adverse_r,
    }


def manage_trade_hybrid_profile(
    candles: pd.DataFrame,
    signal_row: pd.Series,
    horizon: int = 240,
    first_partial_at_r: float = 2.0,
    first_partial_fraction: float = 0.50,
    second_partial_at_r: float = 3.0,
    second_partial_fraction: float = 0.25,
    breakeven_at_r: float = 2.0,
    trail_after_r: float = 3.0,
    trail_lookback: int = 12,
    trail_atr_mult: float = 1.0,
) -> dict:
    idx = int(signal_row["candle_index"])
    side = str(signal_row["side"]).lower()

    entry = float(signal_row["entry"])
    initial_sl = float(signal_row["stop_loss"])

    one_r = abs(entry - initial_sl)

    if one_r <= 0:
        return {
            **signal_row.to_dict(),
            "exit_index": idx,
            "outcome": "invalid_risk",
            "r_result": 0.0,
            "management": "hybrid_profile",
        }

    active_sl = initial_sl

    first_partial_taken = False
    second_partial_taken = False
    breakeven_done = False
    trail_active = False

    realized_r = 0.0
    remaining_fraction = 1.0

    max_favorable_r = 0.0
    max_adverse_r = 0.0

    end = min(len(candles), idx + horizon + 1)

    for i in range(idx + 1, end):
        high = float(candles.iloc[i]["high"])
        low = float(candles.iloc[i]["low"])
        atr = atr_at(candles, i)

        if side == "long":
            favorable_r = (high - entry) / one_r
            adverse_r = (entry - low) / one_r

            max_favorable_r = max(max_favorable_r, favorable_r)
            max_adverse_r = max(max_adverse_r, adverse_r)

            if not breakeven_done and favorable_r >= breakeven_at_r:
                active_sl = max(active_sl, entry)
                breakeven_done = True

            if not first_partial_taken and favorable_r >= first_partial_at_r:
                realized_r += first_partial_fraction * first_partial_at_r
                remaining_fraction -= first_partial_fraction
                first_partial_taken = True

            if not second_partial_taken and favorable_r >= second_partial_at_r:
                realized_r += second_partial_fraction * second_partial_at_r
                remaining_fraction -= second_partial_fraction
                second_partial_taken = True

            if favorable_r >= trail_after_r:
                trail_active = True

            if trail_active:
                proposed_sl = (
                    swing_low(candles, i, trail_lookback)
                    - (atr * trail_atr_mult)
                )
                active_sl = max(active_sl, proposed_sl)

            if low <= active_sl:
                if active_sl >= entry:
                    runner_r = (active_sl - entry) / one_r
                    outcome = "hybrid_exit_profit"
                else:
                    runner_r = -1.0
                    outcome = "loss"

                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": outcome,
                    "r_result": realized_r + (remaining_fraction * runner_r),
                    "management": "hybrid_profile",
                    "first_partial_taken": first_partial_taken,
                    "second_partial_taken": second_partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

        elif side == "short":
            favorable_r = (entry - low) / one_r
            adverse_r = (high - entry) / one_r

            max_favorable_r = max(max_favorable_r, favorable_r)
            max_adverse_r = max(max_adverse_r, adverse_r)

            if not breakeven_done and favorable_r >= breakeven_at_r:
                active_sl = min(active_sl, entry)
                breakeven_done = True

            if not first_partial_taken and favorable_r >= first_partial_at_r:
                realized_r += first_partial_fraction * first_partial_at_r
                remaining_fraction -= first_partial_fraction
                first_partial_taken = True

            if not second_partial_taken and favorable_r >= second_partial_at_r:
                realized_r += second_partial_fraction * second_partial_at_r
                remaining_fraction -= second_partial_fraction
                second_partial_taken = True

            if favorable_r >= trail_after_r:
                trail_active = True

            if trail_active:
                proposed_sl = (
                    swing_high(candles, i, trail_lookback)
                    + (atr * trail_atr_mult)
                )
                active_sl = min(active_sl, proposed_sl)

            if high >= active_sl:
                if active_sl <= entry:
                    runner_r = (entry - active_sl) / one_r
                    outcome = "hybrid_exit_profit"
                else:
                    runner_r = -1.0
                    outcome = "loss"

                return {
                    **signal_row.to_dict(),
                    "exit_index": i,
                    "outcome": outcome,
                    "r_result": realized_r + (remaining_fraction * runner_r),
                    "management": "hybrid_profile",
                    "first_partial_taken": first_partial_taken,
                    "second_partial_taken": second_partial_taken,
                    "breakeven_done": breakeven_done,
                    "trail_active": trail_active,
                    "active_sl": active_sl,
                    "mfe_r": max_favorable_r,
                    "mae_r": max_adverse_r,
                }

    final_close = float(candles.iloc[end - 1]["close"])

    if side == "long":
        runner_r = (final_close - entry) / one_r
    else:
        runner_r = (entry - final_close) / one_r

    return {
        **signal_row.to_dict(),
        "exit_index": end - 1,
        "outcome": "timeout_hybrid",
        "r_result": realized_r + (remaining_fraction * runner_r),
        "management": "hybrid_profile",
        "first_partial_taken": first_partial_taken,
        "second_partial_taken": second_partial_taken,
        "breakeven_done": breakeven_done,
        "trail_active": trail_active,
        "active_sl": active_sl,
        "mfe_r": max_favorable_r,
        "mae_r": max_adverse_r,
    }