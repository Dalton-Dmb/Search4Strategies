from __future__ import annotations

import pandas as pd

from app.execution.signal_engine import generate_signal


def _passes_filters(
    row: pd.Series,
    require_h4_bull: bool = False,
    require_d1_bull: bool = False,
    require_rsi_bull: bool = False,
) -> bool:
    if require_h4_bull and not bool(row.get("h4_ichimoku_bull", False)):
        return False

    if require_d1_bull and not bool(row.get("d1_ichimoku_bull", False)):
        return False

    if require_rsi_bull and not bool(row.get("rsi_bull_regime", False)):
        return False

    return True


def scan_recent_signals(
    features: pd.DataFrame,
    symbol: str,
    timeframe: str,
    rule: str,
    side: str,
    target_r: float = 5.0,
    lookback: int = 300,
    require_h4_bull: bool = False,
    require_d1_bull: bool = False,
    require_rsi_bull: bool = False,
) -> pd.DataFrame:
    rows = []

    df = features.reset_index(drop=True).copy()
    start = max(0, len(df) - lookback)

    for end in range(start + 1, len(df) + 1):
        row = df.iloc[end - 1]

        if not _passes_filters(
            row,
            require_h4_bull=require_h4_bull,
            require_d1_bull=require_d1_bull,
            require_rsi_bull=require_rsi_bull,
        ):
            continue

        window = df.iloc[:end].copy()

        signal = generate_signal(
            features=window,
            symbol=symbol,
            timeframe=timeframe,
            rule=rule,
            side=side,
            target_r=target_r,
        )

        if signal and signal.valid:
            rows.append(signal.__dict__)

    return pd.DataFrame(rows)