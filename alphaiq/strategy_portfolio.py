from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from .domain import FeatureVector, RegimeAssessment, RegimeLabel


class SignalSide(str, Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class ConflictPolicy(str, Enum):
    ABSTAIN = "abstain"
    PREFER_HIGHEST = "prefer_highest"


@dataclass(frozen=True)
class StrategyPortfolioRegistration:
    strategy_id: str
    version: str
    compatible_regimes: Sequence[str]
    required_features: Sequence[str]
    risk_budget_weight: float
    enabled: bool = True
    tags: Sequence[str] = ()

    def __post_init__(self) -> None:
        if self.risk_budget_weight < 0:
            raise ValueError("risk_budget_weight must be >= 0")


@dataclass(frozen=True)
class StrategySignal:
    strategy_id: str
    strategy_version: str
    side: SignalSide
    confidence: float
    quality_score: float
    reason: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class ArbitrationPolicy:
    version: str
    confidence_weight: float
    quality_weight: float
    minimum_confidence: float
    minimum_score: float
    maximum_selected_strategies: int
    conflict_policy: ConflictPolicy
    minimum_conflict_score_gap: float

    def __post_init__(self) -> None:
        if self.confidence_weight < 0 or self.quality_weight < 0:
            raise ValueError("score weights must be >= 0")
        if self.confidence_weight + self.quality_weight <= 0:
            raise ValueError("at least one score weight must be positive")
        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be in [0, 1]")
        if self.maximum_selected_strategies < 1:
            raise ValueError("maximum_selected_strategies must be >= 1")
        if self.minimum_conflict_score_gap < 0:
            raise ValueError("minimum_conflict_score_gap must be >= 0")


@dataclass(frozen=True)
class RankedStrategy:
    strategy_id: str
    strategy_version: str
    side: SignalSide
    score: float
    confidence: float
    risk_allocation_weight: float
    reason: str


@dataclass(frozen=True)
class PortfolioDecision:
    executable: bool
    side: SignalSide
    selected: Sequence[RankedStrategy]
    rejected: Mapping[str, str]
    reason: str
    arbitration_version: str
    regime_label: str


class StrategyPortfolioEngine:
    """Specification-driven strategy eligibility, ranking and arbitration."""

    def __init__(
        self,
        registrations: Mapping[str, StrategyPortfolioRegistration],
        policy: ArbitrationPolicy,
    ) -> None:
        self.registrations = dict(registrations)
        self.policy = policy

    def arbitrate(
        self,
        assessment: RegimeAssessment,
        features: FeatureVector,
        signals: Sequence[StrategySignal],
    ) -> PortfolioDecision:
        if assessment.abstained or assessment.label is RegimeLabel.UNKNOWN:
            return self._no_trade({}, "Regime unresolved", assessment)

        available_features = set(features.values)
        rejected: dict[str, str] = {}
        ranked: list[RankedStrategy] = []

        seen: set[str] = set()
        for signal in signals:
            if signal.strategy_id in seen:
                rejected[signal.strategy_id] = "duplicate_signal"
                continue
            seen.add(signal.strategy_id)
            registration = self.registrations.get(signal.strategy_id)
            if registration is None:
                rejected[signal.strategy_id] = "strategy_not_registered"
                continue
            if not registration.enabled:
                rejected[signal.strategy_id] = "strategy_disabled"
                continue
            if signal.strategy_version != registration.version:
                rejected[signal.strategy_id] = "strategy_version_mismatch"
                continue
            if assessment.label.value not in registration.compatible_regimes:
                rejected[signal.strategy_id] = "regime_not_compatible"
                continue
            if not set(registration.required_features).issubset(available_features):
                rejected[signal.strategy_id] = "required_features_missing"
                continue
            if signal.side is SignalSide.FLAT:
                rejected[signal.strategy_id] = "flat_signal"
                continue
            if signal.confidence < self.policy.minimum_confidence:
                rejected[signal.strategy_id] = "confidence_below_minimum"
                continue

            score = (
                self.policy.confidence_weight * signal.confidence
                + self.policy.quality_weight * signal.quality_score
            ) / (self.policy.confidence_weight + self.policy.quality_weight)
            if score < self.policy.minimum_score:
                rejected[signal.strategy_id] = "score_below_minimum"
                continue

            ranked.append(
                RankedStrategy(
                    strategy_id=signal.strategy_id,
                    strategy_version=signal.strategy_version,
                    side=signal.side,
                    score=score,
                    confidence=signal.confidence,
                    risk_allocation_weight=registration.risk_budget_weight,
                    reason=signal.reason,
                )
            )

        ranked.sort(key=lambda item: (-item.score, item.strategy_id))
        if not ranked:
            return self._no_trade(rejected, "No eligible strategy signal", assessment)

        sides = {item.side for item in ranked}
        if len(sides) > 1:
            if self.policy.conflict_policy is ConflictPolicy.ABSTAIN:
                for item in ranked:
                    rejected[item.strategy_id] = "directional_conflict"
                return self._no_trade(rejected, "Opposing strategy signals", assessment)

            top = ranked[0]
            opposing = next((item for item in ranked[1:] if item.side is not top.side), None)
            if opposing is not None and top.score - opposing.score < self.policy.minimum_conflict_score_gap:
                for item in ranked:
                    rejected[item.strategy_id] = "conflict_score_gap_insufficient"
                return self._no_trade(rejected, "Directional conflict insufficiently resolved", assessment)
            for item in list(ranked):
                if item.side is not top.side:
                    rejected[item.strategy_id] = "opposing_signal_outscored"
            ranked = [item for item in ranked if item.side is top.side]

        selected = ranked[: self.policy.maximum_selected_strategies]
        for item in ranked[self.policy.maximum_selected_strategies :]:
            rejected[item.strategy_id] = "portfolio_capacity_exceeded"

        allocation_total = sum(item.risk_allocation_weight for item in selected)
        if allocation_total <= 0:
            for item in selected:
                rejected[item.strategy_id] = "zero_risk_budget"
            return self._no_trade(rejected, "Selected strategies have no approved risk budget", assessment)

        selected = [
            RankedStrategy(
                strategy_id=item.strategy_id,
                strategy_version=item.strategy_version,
                side=item.side,
                score=item.score,
                confidence=item.confidence,
                risk_allocation_weight=item.risk_allocation_weight / allocation_total,
                reason=item.reason,
            )
            for item in selected
        ]
        return PortfolioDecision(
            executable=True,
            side=selected[0].side,
            selected=tuple(selected),
            rejected=rejected,
            reason="Eligible portfolio selected",
            arbitration_version=self.policy.version,
            regime_label=assessment.label.value,
        )

    def _no_trade(
        self,
        rejected: Mapping[str, str],
        reason: str,
        assessment: RegimeAssessment,
    ) -> PortfolioDecision:
        return PortfolioDecision(
            executable=False,
            side=SignalSide.FLAT,
            selected=(),
            rejected=dict(rejected),
            reason=reason,
            arbitration_version=self.policy.version,
            regime_label=assessment.label.value,
        )
