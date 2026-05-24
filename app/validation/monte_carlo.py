from __future__ import annotations

import math
import random

import pandas as pd


def _is_win(value) -> bool:
    if isinstance(value, bool):
        return value is True
    if isinstance(value, (int, float)):
        return value > 0

    return str(value).strip().lower() in {
        "1", "win", "wins", "tp", "take_profit",
        "target", "profit", "success", "true",
    }


def _is_loss(value) -> bool:
    if isinstance(value, bool):
        return value is False
    if isinstance(value, (int, float)):
        return value < 0

    return str(value).strip().lower() in {
        "-1", "0", "loss", "losses", "sl", "stop_loss",
        "stop", "fail", "failed", "false",
    }


def _get_result_value(label_row: pd.Series):
    for col in [
        "result", "outcome", "label", "target",
        "trade_result", "hit", "win", "is_win",
    ]:
        if col in label_row.index:
            return label_row[col]
    return None


def extract_rule_outcomes(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    rule: str,
    target_r: float,
) -> list[float]:
    features = features.reset_index(drop=True).copy()
    labels = labels.reset_index(drop=True).copy()

    parts = [p.strip() for p in rule.split("AND")]
    outcomes: list[float] = []

    for _, lab in labels.iterrows():
        if "idx" not in lab.index:
            continue

        idx = int(lab["idx"])

        if idx < 0 or idx >= len(features):
            continue

        row = features.iloc[idx]

        if not all(part in row.index and bool(row[part]) for part in parts):
            continue

        result_value = _get_result_value(lab)

        if _is_win(result_value):
            outcomes.append(float(target_r))
        elif _is_loss(result_value):
            outcomes.append(-1.0)

    return outcomes


def max_drawdown(values: list[float]) -> float:
    peak = -math.inf
    worst = 0.0

    for value in values:
        peak = max(peak, value)
        worst = max(worst, peak - value)

    return worst


def max_drawdown_pct(equity: list[float]) -> float:
    peak = -math.inf
    worst = 0.0

    for value in equity:
        peak = max(peak, value)

        if peak > 0:
            dd = (peak - value) / peak
            worst = max(worst, dd)

    return worst


def monte_carlo_simulation(
    outcomes: list[float],
    runs: int = 1000,
    starting_equity_r: float = 0.0,
) -> pd.DataFrame:
    rows = []

    if not outcomes:
        return pd.DataFrame()

    for i in range(runs):
        shuffled = outcomes[:]
        random.shuffle(shuffled)

        equity = []
        current = starting_equity_r

        for r in shuffled:
            current += r
            equity.append(current)

        rows.append({
            "run": i + 1,
            "trades": len(shuffled),
            "ending_r": float(equity[-1]),
            "max_drawdown_r": float(max_drawdown(equity)),
            "min_equity_r": float(min(equity)),
            "max_equity_r": float(max(equity)),
        })

    return pd.DataFrame(rows)


def risk_adjusted_monte_carlo(
    outcomes: list[float],
    runs: int = 1000,
    starting_balance: float = 10000.0,
    risk_per_trade: float = 0.005,
) -> pd.DataFrame:
    rows = []

    if not outcomes:
        return pd.DataFrame()

    for i in range(runs):
        shuffled = outcomes[:]
        random.shuffle(shuffled)

        equity_curve = []
        balance = float(starting_balance)

        for r_multiple in shuffled:
            risk_amount = balance * risk_per_trade
            pnl = risk_amount * r_multiple
            balance += pnl
            equity_curve.append(balance)

        rows.append({
            "run": i + 1,
            "trades": len(shuffled),
            "risk_per_trade": risk_per_trade,
            "starting_balance": starting_balance,
            "ending_balance": float(equity_curve[-1]),
            "net_return_pct": float((equity_curve[-1] / starting_balance) - 1.0),
            "max_drawdown_pct": float(max_drawdown_pct(equity_curve)),
            "min_balance": float(min(equity_curve)),
            "max_balance": float(max(equity_curve)),
        })

    return pd.DataFrame(rows)


def summarize_monte_carlo(results: pd.DataFrame) -> dict:
    if results.empty:
        return {}

    return {
        "runs": int(len(results)),
        "avg_ending_r": float(results["ending_r"].mean()),
        "median_ending_r": float(results["ending_r"].median()),
        "worst_ending_r": float(results["ending_r"].min()),
        "best_ending_r": float(results["ending_r"].max()),
        "avg_max_drawdown_r": float(results["max_drawdown_r"].mean()),
        "worst_max_drawdown_r": float(results["max_drawdown_r"].max()),
        "p05_ending_r": float(results["ending_r"].quantile(0.05)),
        "p95_ending_r": float(results["ending_r"].quantile(0.95)),
        "p95_drawdown_r": float(results["max_drawdown_r"].quantile(0.95)),
    }


def summarize_risk_adjusted(results: pd.DataFrame) -> dict:
    if results.empty:
        return {}

    return {
        "runs": int(len(results)),
        "risk_per_trade_pct": float(results["risk_per_trade"].iloc[0] * 100),
        "avg_ending_balance": float(results["ending_balance"].mean()),
        "median_ending_balance": float(results["ending_balance"].median()),
        "worst_ending_balance": float(results["ending_balance"].min()),
        "best_ending_balance": float(results["ending_balance"].max()),
        "avg_return_pct": float(results["net_return_pct"].mean() * 100),
        "worst_return_pct": float(results["net_return_pct"].min() * 100),
        "best_return_pct": float(results["net_return_pct"].max() * 100),
        "avg_drawdown_pct": float(results["max_drawdown_pct"].mean() * 100),
        "worst_drawdown_pct": float(results["max_drawdown_pct"].max() * 100),
        "p95_drawdown_pct": float(results["max_drawdown_pct"].quantile(0.95) * 100),
    }
