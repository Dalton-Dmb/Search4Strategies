from __future__ import annotations

from datetime import datetime, timezone

import pytest

from alphaiq.contracts import StrategyRegistration
from alphaiq.domain import FeatureVector, MarketSnapshot, OrderIntent, RegimeLabel
from alphaiq.execution import DenyByDefaultRiskPolicy, SimulatedExecutionAdapter
from alphaiq.journal import InMemoryJournal
from alphaiq.pipeline import AlphaIQEngine
from alphaiq.regime import RegistryStrategySelector, RuleBasedRegimeClassifier


class StaticFeatures:
    def build(self, snapshot: MarketSnapshot) -> FeatureVector:
        return FeatureVector(
            timestamp=snapshot.timestamp,
            values={"x": 1.0},
            feature_set_version="test-v1",
            provenance={"source": snapshot.source},
        )


def snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        symbol="XAUUSD",
        timeframe="M15",
        timestamp=datetime(2026, 9, 13, 8, 0, tzinfo=timezone.utc),
        open=3600.0,
        high=3610.0,
        low=3590.0,
        close=3605.0,
        source="test",
    )


def test_snapshot_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        MarketSnapshot("X", "M15", datetime(2026, 1, 1), 1, 2, 0.5, 1.5)


def test_classifier_abstains_without_approved_rules() -> None:
    snap = snapshot()
    features = StaticFeatures().build(snap)
    result = RuleBasedRegimeClassifier().classify(snap, features)
    assert result.label is RegimeLabel.UNKNOWN
    assert result.abstained is True
    assert result.classifier_id == "rule-based-regime"


def test_selector_never_manufactures_unknown_regime_trade() -> None:
    snap = snapshot()
    features = StaticFeatures().build(snap)
    regime = RuleBasedRegimeClassifier().classify(snap, features)
    selector = RegistryStrategySelector({
        "mean-reversion": StrategyRegistration("mean-reversion", "1", ("ranging",), enabled=True)
    })
    decision = selector.select(regime, features)
    assert decision.executable is False
    assert tuple(decision.strategy_ids) == ()


def test_disabled_strategy_cannot_be_selected() -> None:
    from alphaiq.domain import RegimeAssessment

    snap = snapshot()
    features = StaticFeatures().build(snap)
    regime = RegimeAssessment(
        label=RegimeLabel.RANGING,
        confidence=0.8,
        probabilities={"ranging": 0.8},
        evidence={},
        classifier_id="test",
        classifier_version="1",
        timestamp=snap.timestamp,
    )
    selector = RegistryStrategySelector({
        "mean-reversion": StrategyRegistration("mean-reversion", "1", ("ranging",), enabled=False)
    })
    assert selector.select(regime, features).strategy_ids == ()


def test_deny_by_default_risk_vetoes_and_pipeline_journals() -> None:
    snap = snapshot()
    journal = InMemoryJournal()
    engine = AlphaIQEngine(
        feature_engineer=StaticFeatures(),
        classifier=RuleBasedRegimeClassifier(),
        selector=RegistryStrategySelector({}),
        risk_policy=DenyByDefaultRiskPolicy(),
        execution=SimulatedExecutionAdapter(),
        journal=journal,
    )
    intent = OrderIntent("XAUUSD", "buy", 0.01, "market", "test-strategy", "idempotency-1")
    result = engine.process(snap, intent)
    assert result.risk is not None and result.risk.approved is False
    assert result.execution is None
    assert [e.event_type for e in journal.events] == ["regime_assessment", "strategy_decision", "risk_decision"]
    assert len({e.correlation_id for e in journal.events}) == 1


def test_simulated_execution_is_idempotent() -> None:
    adapter = SimulatedExecutionAdapter()
    intent = OrderIntent("XAUUSD", "buy", 0.01, "market", "s", "same-key")
    first = adapter.execute(intent)
    second = adapter.execute(intent)
    assert first == second
