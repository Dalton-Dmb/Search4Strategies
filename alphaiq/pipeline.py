from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

from .contracts import ExecutionAdapter, FeatureEngineer, JournalSink, RegimeClassifier, RiskPolicy, StrategySelector
from .domain import (
    ExecutionReport,
    JournalEvent,
    MarketSnapshot,
    OrderIntent,
    RegimeAssessment,
    RiskDecision,
    StrategyDecision,
)


@dataclass(frozen=True)
class PipelineResult:
    regime: RegimeAssessment
    strategy: StrategyDecision
    risk: RiskDecision | None
    execution: ExecutionReport | None
    correlation_id: str


class AlphaIQEngine:
    """Production orchestration boundary shared by research, paper, shadow and live modes.

    Live behavior is entirely determined by injected adapters/policies and is not enabled here.
    """

    def __init__(
        self,
        feature_engineer: FeatureEngineer,
        classifier: RegimeClassifier,
        selector: StrategySelector,
        risk_policy: RiskPolicy,
        execution: ExecutionAdapter,
        journal: JournalSink,
    ) -> None:
        self.feature_engineer = feature_engineer
        self.classifier = classifier
        self.selector = selector
        self.risk_policy = risk_policy
        self.execution = execution
        self.journal = journal

    def process(self, snapshot: MarketSnapshot, intent: OrderIntent | None = None) -> PipelineResult:
        correlation_id = str(uuid4())
        features = self.feature_engineer.build(snapshot)
        regime = self.classifier.classify(snapshot, features)
        strategy = self.selector.select(regime, features)
        self._record("regime_assessment", asdict(regime), correlation_id)
        self._record("strategy_decision", asdict(strategy), correlation_id)

        risk: RiskDecision | None = None
        execution_report: ExecutionReport | None = None
        if intent is not None:
            risk = self.risk_policy.evaluate(intent, snapshot, regime)
            self._record("risk_decision", asdict(risk), correlation_id)
            if risk.approved:
                execution_report = self.execution.execute(intent)
                self._record("execution_report", asdict(execution_report), correlation_id)

        return PipelineResult(regime, strategy, risk, execution_report, correlation_id)

    def _record(self, event_type: str, payload: dict[str, Any], correlation_id: str) -> None:
        self.journal.append(JournalEvent(event_type=event_type, payload=payload, correlation_id=correlation_id))
