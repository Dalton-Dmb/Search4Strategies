from datetime import datetime, timezone

from alphaiq.domain import FeatureVector, RegimeAssessment, RegimeLabel
from alphaiq.strategy_portfolio import (
    ArbitrationPolicy,
    ConflictPolicy,
    SignalSide,
    StrategyPortfolioEngine,
    StrategyPortfolioRegistration,
    StrategySignal,
)


def assessment(label=RegimeLabel.TRENDING, abstained=False):
    return RegimeAssessment(
        label=label,
        confidence=0.8 if not abstained else None,
        probabilities={label.value: 0.8} if not abstained else {},
        evidence={},
        classifier_id="ensemble",
        classifier_version="1",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        abstained=abstained,
        reason="abstained" if abstained else None,
    )


def features():
    return FeatureVector(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        values={"trend": 1.0, "structure": 1.0},
        feature_set_version="f1",
    )


def policy(conflict_policy=ConflictPolicy.ABSTAIN):
    return ArbitrationPolicy(
        version="1",
        confidence_weight=1.0,
        quality_weight=1.0,
        minimum_confidence=0.5,
        minimum_score=0.5,
        maximum_selected_strategies=2,
        conflict_policy=conflict_policy,
        minimum_conflict_score_gap=0.2,
    )


def registrations():
    return {
        "trend-a": StrategyPortfolioRegistration("trend-a", "1", ["trending"], ["trend"], 2.0),
        "trend-b": StrategyPortfolioRegistration("trend-b", "1", ["trending"], ["structure"], 1.0),
        "range-a": StrategyPortfolioRegistration("range-a", "1", ["ranging"], ["structure"], 1.0),
    }


def test_unresolved_regime_returns_no_trade():
    engine = StrategyPortfolioEngine(registrations(), policy())
    result = engine.arbitrate(assessment(RegimeLabel.UNKNOWN, True), features(), [])
    assert result.executable is False
    assert result.side is SignalSide.FLAT


def test_regime_and_feature_eligibility_are_enforced():
    engine = StrategyPortfolioEngine(registrations(), policy())
    result = engine.arbitrate(
        assessment(),
        features(),
        [
            StrategySignal("range-a", "1", SignalSide.LONG, 0.9, 0.9, "range signal"),
            StrategySignal("trend-a", "1", SignalSide.LONG, 0.9, 0.8, "trend signal"),
        ],
    )
    assert result.executable is True
    assert [item.strategy_id for item in result.selected] == ["trend-a"]
    assert result.rejected["range-a"] == "regime_not_compatible"


def test_opposing_signals_can_force_no_trade():
    engine = StrategyPortfolioEngine(registrations(), policy(ConflictPolicy.ABSTAIN))
    result = engine.arbitrate(
        assessment(),
        features(),
        [
            StrategySignal("trend-a", "1", SignalSide.LONG, 0.9, 0.9, "long"),
            StrategySignal("trend-b", "1", SignalSide.SHORT, 0.9, 0.8, "short"),
        ],
    )
    assert result.executable is False
    assert result.reason == "Opposing strategy signals"


def test_prefer_highest_requires_configured_gap():
    engine = StrategyPortfolioEngine(registrations(), policy(ConflictPolicy.PREFER_HIGHEST))
    result = engine.arbitrate(
        assessment(),
        features(),
        [
            StrategySignal("trend-a", "1", SignalSide.LONG, 1.0, 1.0, "long"),
            StrategySignal("trend-b", "1", SignalSide.SHORT, 0.5, 0.5, "short"),
        ],
    )
    assert result.executable is True
    assert result.side is SignalSide.LONG
    assert result.rejected["trend-b"] == "opposing_signal_outscored"


def test_selected_risk_weights_are_normalized():
    engine = StrategyPortfolioEngine(registrations(), policy())
    result = engine.arbitrate(
        assessment(),
        features(),
        [
            StrategySignal("trend-a", "1", SignalSide.LONG, 0.9, 0.9, "a"),
            StrategySignal("trend-b", "1", SignalSide.LONG, 0.8, 0.8, "b"),
        ],
    )
    assert result.executable is True
    weights = {item.strategy_id: item.risk_allocation_weight for item in result.selected}
    assert weights["trend-a"] == 2 / 3
    assert weights["trend-b"] == 1 / 3
