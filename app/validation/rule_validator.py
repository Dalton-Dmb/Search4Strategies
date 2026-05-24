from __future__ import annotations

import pandas as pd

from app.discovery.rule_miner import mine_boolean_rules


def validate_fixed_rule(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    rule: str,
    min_samples: int = 1,
) -> pd.DataFrame:
    rules = mine_boolean_rules(features, labels, min_samples=min_samples)

    if rules.empty:
        return pd.DataFrame()

    return rules[rules["rule"] == rule].reset_index(drop=True)


def walk_forward_rule_validation(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    rule: str,
    folds: int = 5,
    min_samples: int = 1,
) -> pd.DataFrame:
    features = features.reset_index(drop=True).copy()
    labels = labels.reset_index(drop=True).copy()

    n = len(features)
    fold_size = n // folds

    rows = []

    for i in range(folds):
        start = i * fold_size
        end = n if i == folds - 1 else (i + 1) * fold_size

        feat_fold = features.iloc[start:end].reset_index(drop=True).copy()

        lab_fold = labels[
            (labels["idx"] >= start) &
            (labels["idx"] < end)
        ].copy()

        if lab_fold.empty:
            rows.append({
                "fold": i + 1,
                "samples": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "expectancy_r": 0.0,
                "profit_factor": 0.0,
            })
            continue

        lab_fold["idx"] = lab_fold["idx"] - start
        lab_fold = lab_fold.reset_index(drop=True)

        result = validate_fixed_rule(
            feat_fold,
            lab_fold,
            rule=rule,
            min_samples=min_samples,
        )

        if result.empty:
            rows.append({
                "fold": i + 1,
                "samples": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "expectancy_r": 0.0,
                "profit_factor": 0.0,
            })
        else:
            r = result.iloc[0].to_dict()

            rows.append({
                "fold": i + 1,
                "samples": int(r.get("samples", 0)),
                "wins": int(r.get("wins", 0)),
                "losses": int(r.get("losses", 0)),
                "win_rate": float(r.get("win_rate", 0.0)),
                "expectancy_r": float(r.get("expectancy_r", 0.0)),
                "profit_factor": float(r.get("profit_factor", 0.0)),
            })

    return pd.DataFrame(rows)
