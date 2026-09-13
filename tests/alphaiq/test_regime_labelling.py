import pytest

from alphaiq.regime_labelling import (
    OperationalRegime,
    RegimeEvidence,
    RegimeThresholds,
    label_regime,
)


def cfg(**overrides):
    values = dict(
        version="research-v1",
        strong_trend_min=0.75,
        weak_trend_min=0.55,
        efficiency_min=0.60,
        range_mean_reversion_min=0.70,
        compression_min=0.75,
        expansion_min=0.75,
        transition_min=0.75,
        event_shock_min=0.80,
        chop_liquidity_max=0.30,
        ambiguity_margin=0.05,
        minimum_evidence_count=3,
    )
    values.update(overrides)
    return RegimeThresholds(**values)


def test_insufficient_evidence_abstains():
    result = label_regime(RegimeEvidence(trend_strength=0.9), cfg())
    assert result.regime is OperationalRegime.UNKNOWN
    assert result.reason == "insufficient evidence"


def test_strong_trend_requires_strength_and_efficiency():
    result = label_regime(
        RegimeEvidence(
            trend_strength=0.90,
            directional_efficiency=0.80,
            mean_reversion_score=0.10,
        ),
        cfg(),
    )
    assert result.regime is OperationalRegime.STRONG_TREND
    assert result.threshold_version == "research-v1"


def test_range_mean_reversion_is_first_class_regime():
    result = label_regime(
        RegimeEvidence(
            trend_strength=0.20,
            directional_efficiency=0.25,
            mean_reversion_score=0.92,
            liquidity_quality=0.80,
        ),
        cfg(),
    )
    assert result.regime is OperationalRegime.RANGE
    assert result.confidence > 0.8


def test_event_shock_can_dominate_other_context_when_unambiguous():
    result = label_regime(
        RegimeEvidence(
            trend_strength=0.60,
            directional_efficiency=0.65,
            event_abnormality=0.98,
            transition_score=0.20,
        ),
        cfg(),
    )
    assert result.regime is OperationalRegime.EVENT_SHOCK


def test_materially_ambiguous_candidates_abstain():
    result = label_regime(
        RegimeEvidence(
            compression_score=0.90,
            expansion_score=0.88,
            trend_strength=0.10,
        ),
        cfg(ambiguity_margin=0.05),
    )
    assert result.regime is OperationalRegime.UNKNOWN
    assert "ambiguous" in result.reason


def test_threshold_configuration_is_explicit_and_validated():
    with pytest.raises(ValueError, match="strong trend"):
        cfg(strong_trend_min=0.4, weak_trend_min=0.6)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        cfg(event_shock_min=1.2)
