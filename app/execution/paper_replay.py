from __future__ import annotations

import pandas as pd

from app.execution.managed_trade import (
    manage_trade_hybrid_profile,
)
from app.execution.signal_scanner import scan_recent_signals


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
    require_h4_bull: bool = False,
    require_d1_bull: bool = False,
    require_rsi_bull: bool = False,
) -> pd.DataFrame:

    signals = scan_recent_signals(
        features=features,
        symbol=symbol,
        timeframe=timeframe,
        rule=rule,
        side=side,
        target_r=target_r,
        lookback=lookback,
        require_h4_bull=require_h4_bull,
        require_d1_bull=require_d1_bull,
        require_rsi_bull=require_rsi_bull,
    )

    if signals.empty:
        return pd.DataFrame()

    rows = []

    for _, row in signals.iterrows():

        result = manage_trade_hybrid_profile(
            candles=candles,
            signal_row=row,
            horizon=horizon,
        )

        rows.append(result)

    return pd.DataFrame(rows)


def summarize_replay(df: pd.DataFrame) -> dict:

    if df.empty:
        return {}

    positive = df[df["r_result"] > 0]
    negative = df[df["r_result"] < 0]

    total_r = float(df["r_result"].sum())

    return {
        "total_signals": int(len(df)),
        "wins": int((df["outcome"] == "win").sum()),
        "losses": int((df["outcome"] == "loss").sum()),
        "breakeven_stops": int(
            (df["outcome"] == "breakeven_stop").sum()
        ),
        "ambiguous": int((df["outcome"] == "ambiguous").sum()),
        "timeouts": int(
            df["outcome"].astype(str).str.contains("timeout").sum()
        ),
        "positive_r_trades": int((df["r_result"] > 0).sum()),
        "negative_r_trades": int((df["r_result"] < 0).sum()),
        "total_r": total_r,
        "average_r": float(df["r_result"].mean()),
        "avg_mfe_r": float(df["mfe_r"].mean())
        if "mfe_r" in df.columns
        else 0.0,
        "avg_mae_r": float(df["mae_r"].mean())
        if "mae_r" in df.columns
        else 0.0,
        "profit_factor_proxy": (
            float(positive["r_result"].sum())
            / abs(float(negative["r_result"].sum()))
            if not negative.empty
            else 0.0
        ),
    }