from __future__ import annotations


DEFAULT_PROFILE = {
    "name": "default_fx",
    "atr_stop_mult": 1.0,
    "breakeven_at_r": 2.0,
    "trail_after_r": 3.0,
    "trail_lookback": 12,
    "trail_atr_mult": 1.0,
    "first_partial_at_r": 2.0,
    "first_partial_fraction": 0.50,
    "second_partial_at_r": 3.0,
    "second_partial_fraction": 0.25,
}


PROFILES = {
    "EURUSD": {
        **DEFAULT_PROFILE,
        "name": "eurusd_fx_balanced",
        "atr_stop_mult": 1.0,
        "trail_atr_mult": 1.0,
    },

    "GBPUSD": {
        **DEFAULT_PROFILE,
        "name": "gbpusd_fx_expansion",
        "atr_stop_mult": 1.2,
        "trail_atr_mult": 1.2,
    },

    "USDJPY": {
        **DEFAULT_PROFILE,
        "name": "usdjpy_clean_trend",
        "atr_stop_mult": 1.2,
        "trail_atr_mult": 0.8,
    },

    "NAS100": {
        **DEFAULT_PROFILE,
        "name": "nas100_volatility",
        "atr_stop_mult": 2.5,
        "breakeven_at_r": 3.0,
        "trail_after_r": 4.0,
        "trail_lookback": 16,
        "trail_atr_mult": 2.0,
    },
}


def get_execution_profile(symbol: str) -> dict:
    key = symbol.upper()
    return PROFILES.get(key, DEFAULT_PROFILE).copy()
