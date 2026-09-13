from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

from .contracts import StrategyRegistration
from .domain import FeatureVector, MarketSnapshot, RegimeAssessment, RegimeLabel, StrategyDecision


Rule = Callable[[MarketSnapshot, FeatureVector], RegimeAssessment | None]


class RuleBasedRegimeClassifier:
    classifier_id = "rule-based-regime"

    def __init__(self, rules: Iterable[Rule] = (), version: str = "1.0") -> None:
        self._rules = tuple(rules)
        self.version = version

    def classify(self, snapshot: MarketSnapshot, features: FeatureVector) -> RegimeAssessment:
        for rule in self._rules:
            result = rule(snapshot, features)
            if result is not None:
                return result
        return RegimeAssessment(
            label=RegimeLabel.UNKNOWN,
            confidence=None,
            probabilities={},
            evidence={"configured_rules": len(self._rules)},
            classifier_id=self.classifier_id,
            classifier_version=self.version,
            timestamp=snapshot.timestamp,
            provenance={"feature_set_version": features.feature_set_version},
            abstained=True,
            reason="No approved regime rule matched",
        )


@dataclass
class RegistryStrategySelector:
    registrations: Mapping[str, StrategyRegistration]
    version: str = "1.0"

    def select(self, assessment: RegimeAssessment, features: FeatureVector) -> StrategyDecision:
        if assessment.label is RegimeLabel.UNKNOWN or assessment.abstained:
            return StrategyDecision((), {}, False, "Regime unresolved", self.version)
        available = set(features.values)
        candidates: list[str] = []
        for strategy_id, registration in self.registrations.items():
            if not registration.enabled:
                continue
            if assessment.label.value not in registration.compatible_regimes:
                continue
            if not set(registration.required_features).issubset(available):
                continue
            candidates.append(strategy_id)
        if not candidates:
            return StrategyDecision((), {}, False, "No approved strategy mapping for regime/features", self.version)
        # Ranking/allocation policy is controlled by the specification. Until supplied,
        # candidates are visible to orchestration but not executable.
        return StrategyDecision(tuple(sorted(candidates)), {}, False, "Candidates identified; ranking/allocation is TBD_SPEC", self.version)
