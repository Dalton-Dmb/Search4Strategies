from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence
from uuid import uuid4


class RegimeLabel(str, Enum):
    UNKNOWN = "unknown"
    TRENDING = "trending"
    RANGING = "ranging"
    TRANSITIONAL = "transitional"
    HIGH_VOLATILITY = "high_volatility"


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    source: str = "unknown"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("MarketSnapshot.timestamp must be timezone-aware")
        if self.high < self.low:
            raise ValueError("high must be >= low")
        if not (self.low <= self.open <= self.high and self.low <= self.close <= self.high):
            raise ValueError("open/close must lie within [low, high]")


@dataclass(frozen=True)
class FeatureVector:
    timestamp: datetime
    values: Mapping[str, float | int | bool | None]
    feature_set_version: str
    provenance: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RegimeAssessment:
    label: RegimeLabel
    confidence: float | None
    probabilities: Mapping[str, float]
    evidence: Mapping[str, Any]
    classifier_id: str
    classifier_version: str
    timestamp: datetime
    provenance: Mapping[str, str] = field(default_factory=dict)
    abstained: bool = False
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        for value in self.probabilities.values():
            if not 0.0 <= value <= 1.0:
                raise ValueError("probabilities must be in [0, 1]")


@dataclass(frozen=True)
class StrategyDecision:
    strategy_ids: Sequence[str]
    scores: Mapping[str, float]
    executable: bool
    reason: str
    decision_version: str


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    policy_id: str
    policy_version: str
    constraints: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: str
    quantity: float
    order_type: str
    strategy_id: str
    idempotency_key: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be > 0")
        if not self.idempotency_key:
            raise ValueError("idempotency_key is required")


@dataclass(frozen=True)
class ExecutionReport:
    accepted: bool
    mode: str
    idempotency_key: str
    broker_order_id: str | None = None
    reason: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JournalEvent:
    event_type: str
    payload: Mapping[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = "1.0"
    event_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["timestamp"] = self.timestamp.isoformat()
        return value
