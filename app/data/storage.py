from __future__ import annotations
from pathlib import Path
import pandas as pd

def parquet_path(data_dir: Path, symbol: str, timeframe: str) -> Path:
    return data_dir / symbol.upper() / f"{timeframe.upper()}.parquet"

def save_candles(df: pd.DataFrame, data_dir: Path) -> Path:
    symbol = str(df["symbol"].iloc[0]).upper()
    timeframe = str(df["timeframe"].iloc[0]).upper()
    path = parquet_path(data_dir, symbol, timeframe)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = pd.read_parquet(path)
        df = pd.concat([old, df], ignore_index=True)
    df = df.drop_duplicates(subset=["time","symbol","timeframe"]).sort_values("time").reset_index(drop=True)
    df.to_parquet(path, index=False)
    return path

def load_candles(data_dir: Path, symbol: str, timeframe: str) -> pd.DataFrame:
    path = parquet_path(data_dir, symbol, timeframe)
    if not path.exists():
        raise FileNotFoundError(f"No candle file found: {path}")
    return pd.read_parquet(path).sort_values("time").reset_index(drop=True)

