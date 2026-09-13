from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .domain import ExecutionReport, MarketSnapshot, OrderIntent, RegimeAssessment, RiskDecision


@dataclass
class DenyByDefaultRiskPolicy:
    """Production-safe default until the approved risk specification is loaded."""

    policy_id: str = "deny-by-default"
    version: str = "1.0"

    def evaluate(self, intent: OrderIntent, snapshot: MarketSnapshot, assessment: RegimeAssessment) -> RiskDecision:
        return RiskDecision(
            approved=False,
            reason="Production risk policy is not yet approved/configured (TBD_SPEC)",
            policy_id=self.policy_id,
            policy_version=self.version,
            constraints={"symbol": snapshot.symbol, "regime": assessment.label.value},
        )


@dataclass
class SimulatedExecutionAdapter:
    """Idempotency-aware dry-run execution adapter; never sends live orders."""

    mode: str = "simulation"

    def __post_init__(self) -> None:
        self._seen: dict[str, ExecutionReport] = {}

    def execute(self, intent: OrderIntent) -> ExecutionReport:
        existing = self._seen.get(intent.idempotency_key)
        if existing is not None:
            return existing
        report = ExecutionReport(
            accepted=True,
            mode=self.mode,
            idempotency_key=intent.idempotency_key,
            broker_order_id=None,
            reason="Simulated execution only",
            metadata={"strategy_id": intent.strategy_id, "order_type": intent.order_type},
        )
        self._seen[intent.idempotency_key] = report
        return report
