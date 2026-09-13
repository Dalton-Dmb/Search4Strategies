from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from .domain import (
    ExecutionReport,
    FeatureVector,
    JournalEvent,
    MarketSnapshot,
    OrderIntent,
    RegimeAssessment,
    RiskDecision,
    StrategyDecision,
)


class FeatureEngineer(Protocol):
    def build(self, snapshot: MarketSnapshot) -> FeatureVector: ...


class RegimeClassifier(Protocol):
    classifier_id: str
    version: str

    def classify(self, snapshot: MarketSnapshot, features: FeatureVector) -> RegimeAssessment: ...


class StrategySelector(Protocol):
    version: str

    def select(self, assessment: RegimeAssessment, features: FeatureVector) -> StrategyDecision: ...


class RiskPolicy(Protocol):
    policy_id: str
    version: str

    def evaluate(self, intent: OrderIntent, snapshot: MarketSnapshot, assessment: RegimeAssessment) -> RiskDecision: ...


class ExecutionAdapter(Protocol):
    mode: str

    def execute(self, intent: OrderIntent) -> ExecutionReport: ...


class JournalSink(Protocol):
    def append(self, event: JournalEvent) -> None: ...


class EventContextProvider(Protocol):
    def context_for(self, snapshot: MarketSnapshot) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class StrategyRegistration:
    strategy_id: str
    version: str
    compatible_regimes: Sequence[str]
    required_features: Sequence[str] = ()
    contraindications: Sequence[str] = ()
    enabled: bool = True
