from __future__ import annotations
from pathlib import Path
import json
import pandas as pd

def export_strategy(path: Path, rules: pd.DataFrame, metadata: dict, top_n: int = 10) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": metadata,
        "approved_rules": rules.head(top_n).to_dict(orient="records"),
        "risk_controls": {
            "min_rr": 3,
            "preferred_rr": 10,
            "max_daily_loss": 0.03,
            "max_trades_per_day": 6,
            "stop_after_consecutive_losses": 3
        }
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path

