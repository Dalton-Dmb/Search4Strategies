from __future__ import annotations
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

FEATURE_COLUMNS = [
    "body_pct","upper_wick_pct","lower_wick_pct","direction","engulf_bull","engulf_bear",
    "large_body","rejection_bull","rejection_bear","atr","volatility_rel","swing_high",
    "swing_low","sweep_high","sweep_low","bull_fvg","bear_fvg","session_hour","dow",
    "london","ny","overlap"
]

def train_classifier(features: pd.DataFrame, labels: pd.DataFrame) -> dict:
    X = features.reset_index(drop=True).iloc[labels["idx"].values]
    cols = [c for c in FEATURE_COLUMNS if c in X.columns]
    X = X[cols].fillna(0)
    y = (labels["outcome"].values == 1).astype(int)
    if len(set(y)) < 2:
        raise ValueError("Need both winning and losing examples to train classifier.")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, shuffle=False)
    model = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    report = classification_report(y_test, pred, output_dict=True, zero_division=0)
    importances = pd.DataFrame({"feature": cols, "importance": model.feature_importances_}).sort_values("importance", ascending=False)
    return {"model": model, "report": report, "importances": importances}

