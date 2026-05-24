from __future__ import annotations

from pathlib import Path

import pandas as pd


def summarize_replay_file(path: Path) -> dict:
    df = pd.read_csv(path)

    if df.empty or "r_result" not in df.columns:
        return {}

    positive = float(df.loc[df["r_result"] > 0, "r_result"].sum())
    negative = float(df.loc[df["r_result"] < 0, "r_result"].sum())

    total = int(len(df))
    positive_trades = int((df["r_result"] > 0).sum())
    negative_trades = int((df["r_result"] < 0).sum())

    return {
        "report": str(path),
        "model": path.parent.name,
        "signals": total,
        "positive_trades": positive_trades,
        "negative_trades": negative_trades,
        "positive_execution_rate": positive_trades / total if total else 0.0,
        "total_r": float(df["r_result"].sum()),
        "average_r": float(df["r_result"].mean()),
        "profit_factor": positive / abs(negative) if abs(negative) > 0 else 0.0,
        "avg_mfe_r": float(df["mfe_r"].mean()) if "mfe_r" in df.columns else 0.0,
        "avg_mae_r": float(df["mae_r"].mean()) if "mae_r" in df.columns else 0.0,
        "mfe_mae_ratio": (
            float(df["mfe_r"].mean()) / float(df["mae_r"].mean())
            if "mfe_r" in df.columns
            and "mae_r" in df.columns
            and float(df["mae_r"].mean()) > 0
            else 0.0
        ),
    }


def rank_portfolio_reports(reports_dir: Path) -> pd.DataFrame:
    rows = []

    for path in reports_dir.rglob("paper_replay.csv"):
        summary = summarize_replay_file(path)
        if summary:
            rows.append(summary)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df["score"] = (
        df["profit_factor"].clip(upper=10) * 0.35
        + df["average_r"].clip(lower=-2, upper=5) * 0.25
        + df["positive_execution_rate"] * 0.20
        + df["mfe_mae_ratio"].clip(upper=10) * 0.20
    )

    return df.sort_values(
        ["score", "profit_factor", "average_r"],
        ascending=False,
    ).reset_index(drop=True)
