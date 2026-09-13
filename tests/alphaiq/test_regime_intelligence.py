from datetime import datetime, timezone

from alphaiq.domain import FeatureVector, MarketSnapshot, RegimeAssessment, RegimeLabel
from alphaiq.regime_intelligence import EnsemblePolicy, RegimeEnsembleClassifier


class StaticClassifier:
    def __init__(self, classifier_id: str, label: RegimeLabel, probabilities: dict[str, float], abstained: bool = False):
        self.classifier_id = classifier_id
        self.version = "test-v1"
        self.label = label
        self.probabilities = probabilities
        self.abstained = abstained

    def classify(self, snapshot, features):
        return RegimeAssessment(
            label=self.label,
            confidence=max(self.probabilities.values()) if self.probabilities else None,
            probabilities=self.probabilities,
            evidence={},
            classifier_id=self.classifier_id,
            classifier_version=self.version,
            timestamp=snapshot.timestamp,
            provenance={"feature_set_version": features.feature_set_version},
            abstained=self.abstained,
            reason="test abstention" if self.abstained else None,
        )


def snapshot(minute: int = 0):
    return MarketSnapshot(
        symbol="XAUUSD",
        timeframe="M15",
        timestamp=datetime(2026, 1, 1, 10, minute, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        source="test",
    )


def features(minute: int = 0):
    return FeatureVector(
        timestamp=datetime(2026, 1, 1, 10, minute, tzinfo=timezone.utc),
        values={"x": 1.0},
        feature_set_version="features-v1",
    )


def policy(**overrides):
    values = dict(
        source_weights={"rules": 1.0, "ml": 1.0},
        min_confidence=0.60,
        min_margin=0.10,
        transition_confirmations=2,
        abstain_on_source_disagreement=False,
        version="policy-test-v1",
    )
    values.update(overrides)
    return EnsemblePolicy(**values)


def test_weighted_ensemble_combines_probability_vectors():
    ensemble = RegimeEnsembleClassifier(
        classifiers={
            "rules": StaticClassifier("rules", RegimeLabel.TRENDING, {"trending": 0.8, "ranging": 0.2}),
            "ml": StaticClassifier("ml", RegimeLabel.TRENDING, {"trending": 0.6, "ranging": 0.4}),
        },
        policy=policy(),
    )
    result = ensemble.classify(snapshot(), features())
    assert result.abstained is False
    assert result.label is RegimeLabel.TRENDING
    assert result.probabilities["trending"] == 0.7
    assert result.evidence["policy_version"] == "policy-test-v1"


def test_low_confidence_abstains_fail_safe():
    ensemble = RegimeEnsembleClassifier(
        classifiers={
            "rules": StaticClassifier("rules", RegimeLabel.TRENDING, {"trending": 0.52, "ranging": 0.48}),
            "ml": StaticClassifier("ml", RegimeLabel.TRENDING, {"trending": 0.54, "ranging": 0.46}),
        },
        policy=policy(min_confidence=0.70, min_margin=0.0),
    )
    result = ensemble.classify(snapshot(), features())
    assert result.abstained is True
    assert result.label is RegimeLabel.UNKNOWN
    assert "confidence" in result.reason.lower()


def test_disagreement_can_be_configured_to_abstain():
    ensemble = RegimeEnsembleClassifier(
        classifiers={
            "rules": StaticClassifier("rules", RegimeLabel.TRENDING, {"trending": 0.9, "ranging": 0.1}),
            "ml": StaticClassifier("ml", RegimeLabel.RANGING, {"trending": 0.1, "ranging": 0.9}),
        },
        policy=policy(abstain_on_source_disagreement=True, min_confidence=0.0, min_margin=0.0),
    )
    result = ensemble.classify(snapshot(), features())
    assert result.abstained is True
    assert "disagreement" in result.reason.lower()


def test_transition_requires_configured_confirmations():
    rules = StaticClassifier("rules", RegimeLabel.TRENDING, {"trending": 0.9, "ranging": 0.1})
    ml = StaticClassifier("ml", RegimeLabel.TRENDING, {"trending": 0.8, "ranging": 0.2})
    ensemble = RegimeEnsembleClassifier(
        classifiers={"rules": rules, "ml": ml},
        policy=policy(transition_confirmations=2),
    )

    first = ensemble.classify(snapshot(0), features(0))
    assert first.label is RegimeLabel.TRENDING

    rules.label = RegimeLabel.RANGING
    rules.probabilities = {"trending": 0.1, "ranging": 0.9}
    ml.label = RegimeLabel.RANGING
    ml.probabilities = {"trending": 0.2, "ranging": 0.8}

    pending = ensemble.classify(snapshot(15), features(15))
    assert pending.label is RegimeLabel.TRENDING
    assert pending.evidence["transition_pending"] is True

    confirmed = ensemble.classify(snapshot(30), features(30))
    assert confirmed.label is RegimeLabel.RANGING
    assert confirmed.evidence["transition_pending"] is False


def test_replay_sequence_is_deterministic_after_reset():
    rules = StaticClassifier("rules", RegimeLabel.TRENDING, {"trending": 0.9, "ranging": 0.1})
    ml = StaticClassifier("ml", RegimeLabel.TRENDING, {"trending": 0.8, "ranging": 0.2})
    ensemble = RegimeEnsembleClassifier({"rules": rules, "ml": ml}, policy())

    sequence_a = [ensemble.classify(snapshot(0), features(0)).label]
    rules.label = RegimeLabel.RANGING
    rules.probabilities = {"trending": 0.1, "ranging": 0.9}
    ml.label = RegimeLabel.RANGING
    ml.probabilities = {"trending": 0.2, "ranging": 0.8}
    sequence_a.extend([
        ensemble.classify(snapshot(15), features(15)).label,
        ensemble.classify(snapshot(30), features(30)).label,
    ])

    ensemble.reset()
    rules.label = RegimeLabel.TRENDING
    rules.probabilities = {"trending": 0.9, "ranging": 0.1}
    ml.label = RegimeLabel.TRENDING
    ml.probabilities = {"trending": 0.8, "ranging": 0.2}
    sequence_b = [ensemble.classify(snapshot(0), features(0)).label]
    rules.label = RegimeLabel.RANGING
    rules.probabilities = {"trending": 0.1, "ranging": 0.9}
    ml.label = RegimeLabel.RANGING
    ml.probabilities = {"trending": 0.2, "ranging": 0.8}
    sequence_b.extend([
        ensemble.classify(snapshot(15), features(15)).label,
        ensemble.classify(snapshot(30), features(30)).label,
    ])

    assert sequence_a == sequence_b
