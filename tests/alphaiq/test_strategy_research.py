import pytest

from alphaiq.strategy_research import (
    ImplementationState,
    ManifestOnlyAdapter,
    ResearchSignalSide,
    StrategyResearchContext,
    StrategyResearchRegistry,
    StrategyResearchSpec,
    default_strategy_manifest,
)


def test_default_manifest_contains_first_class_mean_reversion_and_named_project_strategies():
    specs = default_strategy_manifest()
    ids = {s.strategy_id for s in specs}
    assert "range_mean_reversion" in ids
    assert "spoton" in ids
    assert "trinity_steps" in ids
    assert "unicorn" in ids
    assert "golden_goose_smt" in ids


def test_manifest_only_strategy_fails_safe_to_flat():
    spec = next(s for s in default_strategy_manifest() if s.strategy_id == "range_mean_reversion")
    adapter = ManifestOnlyAdapter(spec)
    signal = adapter.evaluate(StrategyResearchContext("RANGE", {"mean_reversion_score": 0.9}, "2026-01-01T00:00:00+00:00"))
    assert signal.side is ResearchSignalSide.FLAT
    assert signal.confidence == 0.0
    assert "abstaining" in signal.reason


def test_registry_requires_regime_and_feature_eligibility():
    registry = StrategyResearchRegistry(default_strategy_manifest())
    eligible = registry.eligible_specs("RANGE", {"mean_reversion_score"})
    ids = {s.strategy_id for s in eligible}
    assert "range_mean_reversion" in ids
    assert "trend_continuation" not in ids


def test_missing_required_features_exclude_strategy():
    registry = StrategyResearchRegistry(default_strategy_manifest())
    eligible = registry.eligible_specs("TRANSITION", {"transition_score"})
    ids = {s.strategy_id for s in eligible}
    assert "reversal_transition" in ids
    assert "trinity_steps" not in ids


def test_duplicate_registration_is_rejected():
    spec = StrategyResearchSpec(
        "x", "1", "test", frozenset({"RANGE"}), frozenset(), ImplementationState.MANIFEST_ONLY
    )
    registry = StrategyResearchRegistry([spec])
    with pytest.raises(ValueError, match="duplicate"):
        registry.register(spec)


def test_unregistered_strategy_lookup_is_explicit_error():
    registry = StrategyResearchRegistry()
    with pytest.raises(KeyError, match="unregistered strategy"):
        registry.get("missing", "1")
