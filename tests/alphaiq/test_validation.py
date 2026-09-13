from datetime import datetime, timedelta, timezone

import pytest

from alphaiq.validation import (
    ResearchObservation,
    assert_chronological,
    assert_point_in_time,
    calculate_metrics,
    deterministic_observation_fingerprint,
    group_metrics,
)


def obs(minutes: int, result: float, regime: str = "RANGE") -> ResearchObservation:
    return ResearchObservation(
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes),
        symbol="XAUUSD",
        timeframe="M15",
        regime=regime,
        strategy_id="mean_reversion",
        strategy_version="1.0.0",
        outcome_r=result,
        feature_fingerprint="features-v1",
        configuration_version="config-v1",
        fold="oos-1",
    )


def test_fingerprint_is_order_independent_but_content_sensitive():
    a, b = obs(0, 1.0), obs(15, -0.5)
    assert deterministic_observation_fingerprint([a, b]) == deterministic_observation_fingerprint([b, a])
    assert deterministic_observation_fingerprint([a]) != deterministic_observation_fingerprint([b])


def test_chronology_and_future_data_guards():
    a, b = obs(0, 1.0), obs(15, -0.5)
    assert_chronological([a, b])
    with pytest.raises(ValueError, match="chronological"):
        assert_chronological([b, a])
    assert_point_in_time([a], a.as_of)
    with pytest.raises(ValueError, match="future"):
        assert_point_in_time([b], a.as_of)


def test_empty_metrics_abstain_instead_of_fabricating_values():
    metrics = calculate_metrics([])
    assert metrics.count == 0
    assert metrics.expectancy_r is None
    assert metrics.profit_factor is None


def test_metrics_and_regime_strategy_grouping_are_reproducible():
    observations = [obs(0, 1.0), obs(15, -0.5), obs(30, 2.0), obs(45, -1.0, "TREND")]
    grouped = group_metrics(observations)
    range_metrics = grouped[("RANGE", "mean_reversion", "1.0.0")]
    assert range_metrics.count == 3
    assert range_metrics.expectancy_r == pytest.approx((1.0 - 0.5 + 2.0) / 3)
    assert range_metrics.win_rate == pytest.approx(2 / 3)
    assert range_metrics.max_drawdown_r == pytest.approx(0.5)


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        ResearchObservation(
            as_of=datetime(2026, 1, 1),
            symbol="XAUUSD",
            timeframe="M15",
            regime="RANGE",
            strategy_id="mean_reversion",
            strategy_version="1.0.0",
            outcome_r=1.0,
            feature_fingerprint="features-v1",
            configuration_version="config-v1",
        )
