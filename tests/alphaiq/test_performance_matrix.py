from datetime import datetime, timedelta, timezone

import pytest

from alphaiq.performance_matrix import MatrixPolicy, build_performance_matrix, rank_supported_cells
from alphaiq.validation import ResearchObservation


def make_obs(i: int, result: float, regime: str = "RANGE", strategy: str = "mean_reversion", fold: str = "oos"):
    return ResearchObservation(
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * i),
        symbol="XAUUSD",
        timeframe="M15",
        regime=regime,
        strategy_id=strategy,
        strategy_version="1.0.0",
        outcome_r=result,
        feature_fingerprint="f-v1",
        configuration_version="c-v1",
        fold=fold,
    )


def test_small_samples_are_reported_but_not_supported_for_inference():
    matrix = build_performance_matrix([make_obs(0, 1.0), make_obs(1, -0.5)], MatrixPolicy("p1", 3))
    cell = next(iter(matrix.values()))
    assert cell.sample_size == 2
    assert cell.eligible_for_inference is False
    assert cell.reason == "insufficient research sample"


def test_supported_cell_contains_reproducible_metrics_and_interval():
    obs = [make_obs(0, 1.0), make_obs(1, -0.5), make_obs(2, 2.0), make_obs(3, 0.5)]
    matrix = build_performance_matrix(obs, MatrixPolicy("p1", 4, 1.96))
    cell = next(iter(matrix.values()))
    assert cell.eligible_for_inference is True
    assert cell.expectancy_r == pytest.approx(0.75)
    assert cell.lower_expectancy_r is not None
    assert cell.upper_expectancy_r is not None
    assert cell.lower_expectancy_r <= cell.expectancy_r <= cell.upper_expectancy_r


def test_folds_are_never_silently_combined():
    obs = [make_obs(0, 1.0, fold="train"), make_obs(1, -1.0, fold="oos")]
    matrix = build_performance_matrix(obs, MatrixPolicy("p1", 1))
    assert len(matrix) == 2
    assert {cell.fold for cell in matrix.values()} == {"train", "oos"}


def test_ranking_excludes_unsupported_cells_and_uses_conservative_bound():
    obs = []
    for i, value in enumerate([1.0, 1.0, 1.0, 1.0]):
        obs.append(make_obs(i, value, regime="TREND", strategy="trend"))
    for i, value in enumerate([2.0, -1.0, 2.0, -1.0], start=10):
        obs.append(make_obs(i, value, regime="RANGE", strategy="range"))
    obs.append(make_obs(20, 10.0, regime="SHOCK", strategy="tiny"))

    matrix = build_performance_matrix(obs, MatrixPolicy("p1", 4))
    ranked = rank_supported_cells(matrix)
    assert len(ranked) == 2
    assert ranked[0].strategy_id == "trend"
    assert all(cell.strategy_id != "tiny" for cell in ranked)


def test_policy_validation_rejects_invalid_sample_and_confidence_values():
    with pytest.raises(ValueError):
        MatrixPolicy("p1", 0)
    with pytest.raises(ValueError):
        MatrixPolicy("p1", 1, 0)
