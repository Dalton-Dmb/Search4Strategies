import pytest

from alphaiq.statistical_robustness import (
    ExcursionObservation,
    StatisticalPolicy,
    calculate_robust_metrics,
    degradation_diagnostic,
)


def test_policy_validation_and_excursion_validation():
    with pytest.raises(ValueError):
        StatisticalPolicy("p1", 0)
    with pytest.raises(ValueError):
        ExcursionObservation(1.0, mfe_r=-1.0)


def test_robust_metrics_include_confidence_and_excursion_analytics():
    observations = [
        ExcursionObservation(1.0, 1.5, 0.4, 600, 120),
        ExcursionObservation(-0.5, 0.2, 0.8, 300, 240),
        ExcursionObservation(2.0, 2.5, 0.3, 900, 180),
        ExcursionObservation(0.5, 1.0, 0.2, 450, 90),
        ExcursionObservation(-0.25, 0.1, 0.5, 200, 150),
    ]
    policy = StatisticalPolicy("p1", periods_per_year=252, bootstrap_samples=200, minimum_sample_size=5)
    metrics = calculate_robust_metrics(observations, policy)
    assert metrics.sample_size == 5
    assert metrics.expectancy_r == pytest.approx(0.55)
    assert metrics.expectancy_ci is not None
    assert metrics.annualized_sharpe is not None
    assert metrics.annualized_sharpe_ci is not None
    assert metrics.annualized_sortino is not None
    assert metrics.max_drawdown_r >= 0
    assert metrics.average_mfe_r == pytest.approx(1.06)
    assert metrics.average_mae_r == pytest.approx(0.44)
    assert metrics.mfe_mae_ratio is not None
    assert metrics.capture_efficiency is not None
    assert metrics.average_time_to_mfe_seconds == pytest.approx(490)
    assert metrics.average_time_to_mae_seconds == pytest.approx(156)
    assert metrics.eligible_for_inference is True


def test_bootstrap_results_are_deterministic_for_same_policy_seed():
    observations = [ExcursionObservation(value) for value in [1, -1, 2, -0.5, 0.75, 0.25]]
    policy = StatisticalPolicy("p1", 252, bootstrap_samples=200, bootstrap_seed=42, minimum_sample_size=2)
    a = calculate_robust_metrics(observations, policy)
    b = calculate_robust_metrics(observations, policy)
    assert a.expectancy_ci == b.expectancy_ci
    assert a.annualized_sharpe_ci == b.annualized_sharpe_ci


def test_minimum_sample_gate_does_not_hide_metrics():
    policy = StatisticalPolicy("p1", 252, bootstrap_samples=100, minimum_sample_size=10)
    metrics = calculate_robust_metrics([ExcursionObservation(1), ExcursionObservation(-0.5)], policy)
    assert metrics.expectancy_r is not None
    assert metrics.eligible_for_inference is False


def test_degradation_diagnostic_tracks_oos_decay():
    diagnostic = degradation_diagnostic({"train": 1.5, "validation": 1.1, "oos": 0.7})
    assert diagnostic.oos_vs_train_change == pytest.approx(-0.8)
    assert diagnostic.oos_vs_validation_change == pytest.approx(-0.4)
