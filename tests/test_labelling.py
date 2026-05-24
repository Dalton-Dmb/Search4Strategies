import pandas as pd
from app.features.candles import add_candle_features
from app.features.structure import add_structure_features
from app.labelling.triple_barrier import label_trades

def test_label_trades_runs():
    df = pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=100, freq="30min", tz="UTC"),
        "open": range(100),
        "high": [x+1 for x in range(100)],
        "low": [x-1 for x in range(100)],
        "close": [x+0.5 for x in range(100)],
        "symbol": "TEST",
        "timeframe": "M30",
        "tick_volume": 1,
        "spread": 1,
        "real_volume": 0,
    })
    feat = add_structure_features(add_candle_features(df))
    labels = label_trades(feat, side=1, target_r=3, horizon=10)
    assert not labels.empty
    assert {"entry","sl","tp","outcome","realized_r"}.issubset(labels.columns)

