from __future__ import annotations
from app.execution.managed_trade import (
    manage_trade_atr_profile,
    manage_trade_runner_profile,
    manage_trade_hybrid_profile,
)
import pandas as pd

from app.execution.signal_scanner import scan_recent_signals
from app.execution.managed_trade import (
    manage_trade_atr_profile,
    manage_trade_runner_profile,
)

def replay_signal_outcome(
    candles: pd.DataFrame,
    signal_row: pd.Series,
    horizon: int = 120,
) -> dict:
    return manage_trade_hybrid_profile(
        candles=candles,
        signal_row=signal_row,
        horizon=horizon,
    )


def replay_recent_signals(
    candles: pd.DataFrame,
    features: pd.DataFrame,
    symbol: str,
    timeframe: str,
    rule: str,
    side: str,
    target_r: float = 5.0,
    lookback: int = 1000,
    horizon: int = 120,
) -> pd.DataFrame:
    signals = scan_recent_signals(
        features=features,
        symbol=symbol,
        timeframe=timeframe,
        rule=rule,
        side=side,
        target_r=target_r,
        lookback=lookback,
    )

    if signals.empty:
        return pd.DataFrame()

    candles = candles.reset_index(drop=True).copy()

    rows = []

    for _, signal in signals.iterrows():
        rows.append(
            replay_signal_outcome(
                candles=candles,
                signal_row=signal,
                horizon=horizon,
            )
        )

    return pd.DataFrame(rows)


def summarize_replay(results: pd.DataFrame) -> dict:
    if results.empty:
        return {}

    positive = float(results.loc[results["r_result"] > 0, "r_result"].sum())
    negative = float(results.loc[results["r_result"] < 0, "r_result"].sum())

    return {
        "total_signals": int(len(results)),
        "wins": int((results["outcome"] == "win").sum()),
        "losses": int((results["outcome"] == "loss").sum()),
        "breakeven_stops": int((results["outcome"] == "breakeven_stop").sum()),
        "ambiguous": int((results["outcome"] == "ambiguous_both_hit").sum()),
        "timeouts": int((results["outcome"] == "timeout").sum()),
        "positive_r_trades": int((results["r_result"] > 0).sum()),
        "negative_r_trades": int((results["r_result"] < 0).sum()),
        "total_r": float(results["r_result"].sum()),
        "average_r": float(results["r_result"].mean()),
        "avg_mfe_r": float(results["mfe_r"].mean()) if "mfe_r" in results.columns else 0.0,
        "avg_mae_r": float(results["mae_r"].mean()) if "mae_r" in results.columns else 0.0,
        "profit_factor_proxy": positive / abs(negative) if abs(negative) > 0 else 0.0,
    }
