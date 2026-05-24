from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

def write_discovery_report(reports_dir: Path, name: str, rules: pd.DataFrame, summary: dict, importances: pd.DataFrame | None = None) -> Path:
    target = reports_dir / name
    target.mkdir(parents=True, exist_ok=True)
    (target / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    rules.to_csv(target / "rules.csv", index=False)
    if importances is not None:
        importances.to_csv(target / "feature_importance.csv", index=False)
    if not rules.empty:
        top = rules.head(20).iloc[::-1]
        plt.figure(figsize=(10, 6))
        plt.barh(top["rule"], top["expectancy_r"])
        plt.title("Top Rules by Expectancy R")
        plt.tight_layout()
        plt.savefig(target / "top_rules.png")
        plt.close()
    return target

