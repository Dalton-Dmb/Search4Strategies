from __future__ import annotations
import pandas as pd

def walk_forward_slices(n: int, train: int, test: int):
    start = 0
    while start + train + test <= n:
        yield slice(start, start + train), slice(start + train, start + train + test)
        start += test

def summarize_labels(labels: pd.DataFrame) -> dict:
    total = len(labels)
    wins = int((labels["outcome"] == 1).sum())
    losses = int((labels["outcome"] == -1).sum())
    return {
        "trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / total if total else 0,
        "expectancy_r": float(labels["realized_r"].mean()) if total else 0,
        "max_drawdown_r": float((labels["realized_r"].cumsum() - labels["realized_r"].cumsum().cummax()).min()) if total else 0,
    }

