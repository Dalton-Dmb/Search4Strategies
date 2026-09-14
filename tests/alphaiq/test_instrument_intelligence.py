from datetime import datetime, timedelta, timezone

import pytest

from alphaiq.instrument_intelligence import (
    EmpiricalMapPolicy,
    EmpiricalObservation,
    InstrumentSpec,
    InstrumentUniverse,
    RankingWeights,
    build_empirical_map,
    default_research_universe,
    rank_engine_instruments,
)
from alphaiq.validation import ResearchObservation


def make_obs(
    i: int,
    symbol: str,
    strategy: str,
    result: float,
    regime: str = "STRONG_TREND",
    fold: str = "oos",
    thesis_tf: str = "H1",
    entry_tf: str = "M15",
    mfe: float | None = 1.5,
    mae: float | None = 0.5,
    slippage: float | None = 0.01,
):
    base = ResearchObservation(
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * i),
        symbol=symbol,
        timeframe=entry_tf,
        regime=regime,
        strategy_id=strategy,
        strategy_version="1.0.0",
        outcome_r=result,
        feature_fingerprint="f-v1",
        configuration_version="c-v1",
        fold=fold,
    )
    return EmpiricalObservation(
        research=base,
        thesis_timeframe=thesis_tf,
        entry_timeframe=entry_tf,
        session="LONDON",
        event_state="normal",
        mfe_r=mfe,
        mae_r=mae,
        slippage_r=slippage,
        latency_ms=25.0,
    )


def test_default_universe_is_gold_prioritised_but_multi_asset():
    universe = default_research_universe()
    symbols = universe.enabled_symbols()
    assert symbols[0] == "XAUUSD"
    assert "XAUGBP" in symbols
    assert "XAUEUR" in symbols
    assert "XAUJPY" in symbols
    assert "USDJPY" in symbols
    assert "EURCHF" in symbols
    assert "NZDUSD" in symbols


def test_broker_aliases_are_configuration_not_strategy_logic():
    spec = InstrumentSpec(
        "XAUUSD",
        "METAL",
        100,
        broker_aliases={"pepperstone": "XAUUSD", "example": "GOLD.cash"},
    )
    assert spec.symbol_for_broker("example") == "GOLD.cash"
    assert spec.symbol_for_broker("unknown") == "XAUUSD"


def test_universe_rejects_duplicate_canonical_symbols():
    with pytest.raises(ValueError):
        InstrumentUniverse(
            "u1",
            (
                InstrumentSpec("XAUUSD", "METAL", 100),
                InstrumentSpec("XAUUSD", "METAL", 90),
            ),
        )


def test_empirical_map_separates_instrument_regime_and_timeframe_dimensions():
    obs = [
        make_obs(0, "XAUUSD", "trend", 1.0, thesis_tf="H1", entry_tf="M15"),
        make_obs(1, "XAUUSD", "trend", 0.5, thesis_tf="H1", entry_tf="M30"),
        make_obs(2, "USDJPY", "trend", 1.2, thesis_tf="H1", entry_tf="M15"),
        make_obs(3, "XAUUSD", "trend", -0.2, regime="RANGE", thesis_tf="H1", entry_tf="M15"),
    ]
    matrix = build_empirical_map(obs, EmpiricalMapPolicy("p1", minimum_sample_size=1))
    assert len(matrix) == 4
    assert {cell.symbol for cell in matrix.values()} == {"XAUUSD", "USDJPY"}
    assert {cell.entry_timeframe for cell in matrix.values()} == {"M15", "M30"}
    assert {cell.regime for cell in matrix.values()} == {"STRONG_TREND", "RANGE"}


def test_empirical_cell_includes_sharpe_sortino_mfe_mae_and_execution_metrics():
    obs = [
        make_obs(0, "XAUUSD", "trend", 1.0, mfe=2.0, mae=0.4, slippage=0.01),
        make_obs(1, "XAUUSD", "trend", -0.5, mfe=0.5, mae=0.8, slippage=0.02),
        make_obs(2, "XAUUSD", "trend", 1.5, mfe=2.0, mae=0.3, slippage=0.01),
        make_obs(3, "XAUUSD", "trend", -0.25, mfe=0.7, mae=0.6, slippage=0.03),
    ]
    matrix = build_empirical_map(obs, EmpiricalMapPolicy("p1", minimum_sample_size=4))
    cell = next(iter(matrix.values()))
    assert cell.eligible_for_inference is True
    assert cell.sharpe_like is not None
    assert cell.sortino_like is not None
    assert cell.average_mfe_r == pytest.approx(1.3)
    assert cell.average_mae_r == pytest.approx(0.525)
    assert cell.capture_efficiency is not None
    assert cell.average_slippage_r == pytest.approx(0.0175)
    assert cell.average_latency_ms == pytest.approx(25.0)
    assert cell.lower_expectancy_r <= cell.expectancy_r <= cell.upper_expectancy_r


def test_insufficient_cells_are_not_ranked():
    obs = [make_obs(0, "XAUUSD", "trend", 5.0)]
    matrix = build_empirical_map(obs, EmpiricalMapPolicy("p1", minimum_sample_size=2))
    leaderboard = rank_engine_instruments(
        matrix,
        RankingWeights(1.0, 0.5, 0.25, 0.25, 0.25, 0.25),
    )
    assert leaderboard == {}


def test_engine_instrument_ranking_can_discover_pair_specialisation():
    obs = []
    xau = [0.4, 0.5, 0.6, -0.2, 0.7, 0.3]
    jpy = [1.0, 1.1, 0.9, -0.1, 1.2, 0.8]
    for i, value in enumerate(xau):
        obs.append(make_obs(i, "XAUUSD", "trend", value, mfe=1.5, mae=0.5))
    for i, value in enumerate(jpy, start=20):
        obs.append(make_obs(i, "USDJPY", "trend", value, mfe=1.6, mae=0.4))

    matrix = build_empirical_map(obs, EmpiricalMapPolicy("p1", minimum_sample_size=6))
    leaderboard = rank_engine_instruments(
        matrix,
        RankingWeights(
            conservative_expectancy=1.0,
            sharpe_like=0.2,
            sortino_like=0.1,
            profit_factor=0.05,
            drawdown_penalty=0.1,
            slippage_penalty=0.1,
        ),
    )
    rows = leaderboard[("trend", "1.0.0")]
    assert rows[0].symbol == "USDJPY"
    assert rows[0].productivity_score > rows[1].productivity_score


def test_observation_rejects_negative_excursion_magnitudes():
    with pytest.raises(ValueError):
        make_obs(0, "XAUUSD", "trend", 1.0, mfe=-1.0)
