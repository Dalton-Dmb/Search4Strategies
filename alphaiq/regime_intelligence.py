from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .contracts import RegimeClassifier
from .domain import FeatureVector, MarketSnapshot, RegimeAssessment, RegimeLabel


@dataclass(frozen=True)
class EnsemblePolicy:
    """Explicit, specification-controlled ensemble policy.

    No numeric decision threshold is hidden in the implementation. Callers must
    provide the confidence, margin and persistence requirements approved by the
    AlphaIQ specification/configuration layer.
    """

    source_weights: Mapping[str, float]
    min_confidence: float
    min_margin: float
    transition_confirmations: int
    abstain_on_source_disagreement: bool
    version: str

    def __post_init__(self) -> None:
        if not self.source_weights:
            raise ValueError("source_weights must not be empty")
        if any(weight <= 0 for weight in self.source_weights.values()):
            raise ValueError("all source weights must be > 0")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        if not 0.0 <= self.min_margin <= 1.0:
            raise ValueError("min_margin must be in [0, 1]")
        if self.transition_confirmations < 1:
            raise ValueError("transition_confirmations must be >= 1")
        if not self.version:
            raise ValueError("policy version is required")


@dataclass
class TransitionState:
    accepted_label: RegimeLabel = RegimeLabel.UNKNOWN
    pending_label: RegimeLabel = RegimeLabel.UNKNOWN
    confirmations: int = 0


@dataclass(frozen=True)
class EnsembleTrace:
    source_assessments: Sequence[RegimeAssessment]
    weighted_probabilities: Mapping[str, float]
    top_label: RegimeLabel
    top_probability: float
    runner_up_probability: float
    disagreement: bool
    transition_pending: bool
    transition_confirmations: int


@dataclass
class RegimeEnsembleClassifier:
    """Combines deterministic and ML regime evidence with fail-safe abstention.

    The ensemble is stateful only for transition persistence/hysteresis. Given
    the same ordered input sequence and policy it is deterministic and replayable.
    """

    classifiers: Mapping[str, RegimeClassifier]
    policy: EnsemblePolicy
    classifier_id: str = "regime-ensemble"
    state: TransitionState = field(default_factory=TransitionState)

    def __post_init__(self) -> None:
        missing = set(self.policy.source_weights) - set(self.classifiers)
        if missing:
            raise ValueError(f"policy weights reference unknown classifiers: {sorted(missing)}")

    def reset(self) -> None:
        self.state = TransitionState()

    def classify(self, snapshot: MarketSnapshot, features: FeatureVector) -> RegimeAssessment:
        assessments = tuple(
            self.classifiers[source_id].classify(snapshot, features)
            for source_id in self.policy.source_weights
        )
        usable = tuple(a for a in assessments if not a.abstained and a.probabilities)
        if not usable:
            return self._abstain(snapshot, features, assessments, "No classifier supplied usable regime probabilities")

        weighted: dict[str, float] = {}
        weight_total = 0.0
        source_labels: set[RegimeLabel] = set()
        for source_id, weight in self.policy.source_weights.items():
            assessment = next(a for a in assessments if a.classifier_id == self.classifiers[source_id].classifier_id)
            if assessment.abstained or not assessment.probabilities:
                continue
            weight_total += weight
            if assessment.label is not RegimeLabel.UNKNOWN:
                source_labels.add(assessment.label)
            for label, probability in assessment.probabilities.items():
                weighted[label] = weighted.get(label, 0.0) + weight * float(probability)

        if weight_total <= 0:
            return self._abstain(snapshot, features, assessments, "All configured ensemble sources abstained")

        weighted = {label: value / weight_total for label, value in weighted.items()}
        ranked = sorted(weighted.items(), key=lambda item: (-item[1], item[0]))
        if not ranked:
            return self._abstain(snapshot, features, assessments, "Ensemble produced no regime probabilities")

        top_name, top_probability = ranked[0]
        runner_up_probability = ranked[1][1] if len(ranked) > 1 else 0.0
        try:
            proposed = RegimeLabel(top_name)
        except ValueError:
            return self._abstain(snapshot, features, assessments, f"Unknown regime label from ensemble: {top_name}")

        disagreement = len(source_labels) > 1
        margin = top_probability - runner_up_probability
        if self.policy.abstain_on_source_disagreement and disagreement:
            return self._abstain(snapshot, features, assessments, "Classifier disagreement requires abstention", weighted)
        if top_probability < self.policy.min_confidence:
            return self._abstain(snapshot, features, assessments, "Ensemble confidence below configured minimum", weighted)
        if margin < self.policy.min_margin:
            return self._abstain(snapshot, features, assessments, "Top-regime margin below configured minimum", weighted)

        accepted, pending = self._apply_hysteresis(proposed)
        evidence = {
            "policy_version": self.policy.version,
            "source_labels": [label.value for label in sorted(source_labels, key=lambda item: item.value)],
            "disagreement": disagreement,
            "top_probability": top_probability,
            "runner_up_probability": runner_up_probability,
            "margin": margin,
            "proposed_label": proposed.value,
            "transition_pending": pending,
            "transition_confirmations": self.state.confirmations,
            "source_assessments": [
                {
                    "classifier_id": a.classifier_id,
                    "classifier_version": a.classifier_version,
                    "label": a.label.value,
                    "confidence": a.confidence,
                    "abstained": a.abstained,
                    "reason": a.reason,
                }
                for a in assessments
            ],
        }
        return RegimeAssessment(
            label=accepted,
            confidence=top_probability,
            probabilities=weighted,
            evidence=evidence,
            classifier_id=self.classifier_id,
            classifier_version=self.policy.version,
            timestamp=snapshot.timestamp,
            provenance={"feature_set_version": features.feature_set_version},
            abstained=False,
            reason="Transition confirmation pending" if pending else None,
        )

    def _apply_hysteresis(self, proposed: RegimeLabel) -> tuple[RegimeLabel, bool]:
        if self.state.accepted_label is RegimeLabel.UNKNOWN:
            self.state.accepted_label = proposed
            self.state.pending_label = RegimeLabel.UNKNOWN
            self.state.confirmations = 0
            return proposed, False

        if proposed is self.state.accepted_label:
            self.state.pending_label = RegimeLabel.UNKNOWN
            self.state.confirmations = 0
            return self.state.accepted_label, False

        if proposed is self.state.pending_label:
            self.state.confirmations += 1
        else:
            self.state.pending_label = proposed
            self.state.confirmations = 1

        if self.state.confirmations >= self.policy.transition_confirmations:
            self.state.accepted_label = proposed
            self.state.pending_label = RegimeLabel.UNKNOWN
            self.state.confirmations = 0
            return proposed, False

        return self.state.accepted_label, True

    def _abstain(
        self,
        snapshot: MarketSnapshot,
        features: FeatureVector,
        assessments: Sequence[RegimeAssessment],
        reason: str,
        probabilities: Mapping[str, float] | None = None,
    ) -> RegimeAssessment:
        return RegimeAssessment(
            label=RegimeLabel.UNKNOWN,
            confidence=None,
            probabilities=probabilities or {},
            evidence={
                "policy_version": self.policy.version,
                "sources": [
                    {
                        "classifier_id": a.classifier_id,
                        "classifier_version": a.classifier_version,
                        "label": a.label.value,
                        "abstained": a.abstained,
                        "reason": a.reason,
                    }
                    for a in assessments
                ],
            },
            classifier_id=self.classifier_id,
            classifier_version=self.policy.version,
            timestamp=snapshot.timestamp,
            provenance={"feature_set_version": features.feature_set_version},
            abstained=True,
            reason=reason,
        )
