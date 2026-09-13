"""Integrated paper/shadow validation harness for AlphaIQ™ research.

The harness records what the system would have decided and later attaches an
observed research outcome. It never submits orders and never converts a shadow
decision into a brokerage action.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from hashlib import sha256
import json
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class ShadowDecision:
    decision_id: str
    as_of: datetime
    symbol: str
    timeframe: str
    regime: str
    regime_confidence: float
    strategy_id: str | None
    strategy_version: str | None
    research_side: str
    feature_fingerprint: str
    configuration_version: str
    model_version: str | None = None
    reason: str = ""
    outcome_r: float | None = None

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if not 0.0 <= self.regime_confidence <= 1.0:
            raise ValueError("regime_confidence must be normalized to [0, 1]")
        if not self.decision_id or not self.symbol or not self.timeframe:
            raise ValueError("decision identity and market coordinates are required")
        if not self.feature_fingerprint or not self.configuration_version:
            raise ValueError("feature/configuration lineage is required")
        if self.research_side not in {"LONG", "SHORT", "FLAT"}:
            raise ValueError("research_side must be LONG, SHORT or FLAT")
        if self.research_side == "FLAT" and self.strategy_id is not None:
            # A strategy may be named while abstaining, but it must preserve version lineage.
            if not self.strategy_version:
                raise ValueError("strategy version required when strategy_id is present")

    def canonical(self) -> Mapping[str, object]:
        return {
            "decision_id": self.decision_id,
            "as_of": self.as_of.isoformat(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "regime": self.regime,
            "regime_confidence": self.regime_confidence,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "research_side": self.research_side,
            "feature_fingerprint": self.feature_fingerprint,
            "configuration_version": self.configuration_version,
            "model_version": self.model_version,
            "reason": self.reason,
            "outcome_r": self.outcome_r,
        }


class ShadowLedger:
    def __init__(self) -> None:
        self._decisions: dict[str, ShadowDecision] = {}

    def record(self, decision: ShadowDecision) -> None:
        if decision.decision_id in self._decisions:
            raise ValueError(f"duplicate decision_id: {decision.decision_id}")
        self._decisions[decision.decision_id] = decision

    def attach_outcome(self, decision_id: str, outcome_r: float) -> None:
        current = self._decisions[decision_id]
        if current.outcome_r is not None:
            raise ValueError("outcome already attached")
        self._decisions[decision_id] = replace(current, outcome_r=outcome_r)

    def decisions(self) -> tuple[ShadowDecision, ...]:
        return tuple(sorted(self._decisions.values(), key=lambda d: (d.as_of, d.decision_id)))

    def fingerprint(self) -> str:
        payload = json.dumps(
            [d.canonical() for d in self.decisions()],
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return sha256(payload.encode("utf-8")).hexdigest()


def shadow_summary(decisions: Iterable[ShadowDecision]) -> Mapping[str, float | int]:
    rows = tuple(decisions)
    total = len(rows)
    flat = sum(1 for d in rows if d.research_side == "FLAT")
    with_outcome = [d.outcome_r for d in rows if d.outcome_r is not None]
    return {
        "decisions": total,
        "flat_decisions": flat,
        "abstention_rate": (flat / total) if total else 0.0,
        "outcomes_attached": len(with_outcome),
        "mean_outcome_r": (sum(with_outcome) / len(with_outcome)) if with_outcome else 0.0,
    }
