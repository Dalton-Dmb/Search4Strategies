from __future__ import annotations

import pandas as pd

from app.execution.signal_engine import generate_signal


def scan_recent_signals(
    features: pd.DataFrame,
    symbol: str,
    timeframe: str,
    rule: str,
    side: str,
    target_r: float = 5.0,
    lookback: int = 300,
) -> pd.DataFrame:
    rows = []

    df = features.reset_index(drop=True).copy()
    start = max(0, len(df) - lookback)

    for end in range(start + 1, len(df) + 1):
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
