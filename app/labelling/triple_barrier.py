from __future__ import annotations
import numpy as np
import pandas as pd

def label_trades(
    df: pd.DataFrame,
    side: int,
    target_r: float = 3.0,
    horizon: int = 48,
    atr_mult: float = 1.5,
) -> pd.DataFrame:
    """
    Labels every candle as a hypothetical long or short entry.
    side=1 for long, side=-1 for short.
    """
    if side not in (1, -1):
        raise ValueError("side must be 1 or -1")
    rows = []
    n = len(df)
    for i in range(n - horizon - 1):
        entry = float(df["close"].iloc[i])
        atr = float(df["atr"].iloc[i]) if "atr" in df else float(df["high"].iloc[i] - df["low"].iloc[i])
        risk = max(atr * atr_mult, 1e-10)
        sl = entry - side * risk
        tp = entry + side * risk * target_r
        future = df.iloc[i+1:i+1+horizon]
        outcome = 0
        hit_bar = None
        mfe = 0.0
        mae = 0.0
        for j, row in enumerate(future.itertuples(index=False), start=1):
            high = float(getattr(row, "high"))
            low = float(getattr(row, "low"))
            if side == 1:
                mfe = max(mfe, (high - entry) / risk)
                mae = min(mae, (low - entry) / risk)
                hit_sl = low <= sl
                hit_tp = high >= tp
            else:
                mfe = max(mfe, (entry - low) / risk)
                mae = min(mae, (entry - high) / risk)
                hit_sl = high >= sl
                hit_tp = low <= tp
            if hit_sl and hit_tp:
                outcome = -1
                hit_bar = j
                break
            if hit_tp:
                outcome = 1
                hit_bar = j
                break
            if hit_sl:
                outcome = -1
                hit_bar = j
                break
        rows.append({
            "idx": i,
            "time": df["time"].iloc[i],
            "side": side,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "risk": risk,
            "target_r": target_r,
            "horizon": horizon,
            "outcome": outcome,
            "hit_bar": hit_bar or horizon,
            "mfe_r": mfe,
            "mae_r": mae,
            "realized_r": target_r if outcome == 1 else (-1 if outcome == -1 else 0),
        })
    return pd.DataFrame(rows)

