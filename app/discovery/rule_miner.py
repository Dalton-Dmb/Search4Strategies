from __future__ import annotations
import itertools
import pandas as pd

CANDIDATE_FEATURES = [
    "engulf_bull","engulf_bear","large_body","rejection_bull","rejection_bear",
    "sweep_high","sweep_low","bull_fvg","bear_fvg","london","ny","overlap"
]

def mine_boolean_rules(features: pd.DataFrame, labels: pd.DataFrame, min_samples: int = 40) -> pd.DataFrame:
    joined = features.reset_index(drop=True).iloc[labels["idx"].values].copy()
    joined["outcome"] = labels["outcome"].values
    joined["realized_r"] = labels["realized_r"].values

    feats = [f for f in CANDIDATE_FEATURES if f in joined.columns]
    rules = []
    for k in [1, 2, 3]:
        for combo in itertools.combinations(feats, k):
            mask = joined[list(combo)].eq(1).all(axis=1)
            sample = joined[mask]
            if len(sample) < min_samples:
                continue
            wins = int((sample["outcome"] == 1).sum())
            losses = int((sample["outcome"] == -1).sum())
            wr = wins / len(sample)
            expectancy = sample["realized_r"].mean()
            gross_win = sample.loc[sample["realized_r"] > 0, "realized_r"].sum()
            gross_loss = abs(sample.loc[sample["realized_r"] < 0, "realized_r"].sum())
            pf = gross_win / gross_loss if gross_loss else float("inf")
            rules.append({
                "rule": " AND ".join(combo),
                "samples": len(sample),
                "wins": wins,
                "losses": losses,
                "win_rate": wr,
                "expectancy_r": expectancy,
                "profit_factor": pf,
            })
    return pd.DataFrame(rules).sort_values(["expectancy_r","profit_factor","samples"], ascending=[False,False,False])

