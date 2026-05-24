from __future__ import annotations

import pandas as pd

from app.features.ichimoku import add_ichimoku_features


def _normalize_time(series: pd.Series) -> pd.Series:
    return (
        pd.to_datetime(series, utc=True)
        .dt.tz_convert(None)
        .astype("datetime64[ns]")
    )


def build_htf_bias(
    htf_df: pd.DataFrame,
    prefix: str,
) -> pd.DataFrame:
    df = add_ichimoku_features(htf_df.copy())

    out = df[
        [
            "time",
            "ichimoku_bull",
            "ichimoku_bear",
        ]
    ].copy()

    out["time"] = _normalize_time(out["time"])

    out = out.rename(
        columns={
            "ichimoku_bull": f"{prefix}_ichimoku_bull",
            "ichimoku_bear": f"{prefix}_ichimoku_bear",
        }
    )

    return out.sort_values("time").reset_index(drop=True)


def merge_mtf_bias(
    ltf_df: pd.DataFrame,
    h4_df: pd.DataFrame | None = None,
    d1_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    out = ltf_df.copy()
    out["time"] = _normalize_time(out["time"])
    out = out.sort_values("time").reset_index(drop=True)

    if h4_df is not None:
        h4_bias = build_htf_bias(h4_df, "h4")

        out = pd.merge_asof(
            out,
            h4_bias,
            on="time",
            direction="backward",
        )

    if d1_df is not None:
        d1_bias = build_htf_bias(d1_df, "d1")

        out = pd.merge_asof(
            out,
            d1_bias,
            on="time",
            direction="backward",
        )

    for col in [
        "h4_ichimoku_bull",
        "h4_ichimoku_bear",
        "d1_ichimoku_bull",
        "d1_ichimoku_bear",
    ]:
        if col in out.columns:
            out[col] = out[col].fillna(False).astype(bool)

    return out
