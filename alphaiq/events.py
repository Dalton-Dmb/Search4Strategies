from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping, Protocol, Sequence

from .domain import MarketSnapshot


class EventSeverity(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass(frozen=True)
class MarketEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    severity: EventSeverity
    source: str
    surprise: float | None = None
    metadata: Mapping[str, object] | None = None


class EventProvider(Protocol):
    def events_for(self, snapshot: MarketSnapshot) -> Sequence[MarketEvent]: ...


class NoOpEventProvider:
    def events_for(self, snapshot: MarketSnapshot) -> Sequence[MarketEvent]:
        return ()
