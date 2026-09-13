from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Iterable, Mapping, Sequence

from .events import EventSeverity, MarketEvent


@dataclass(frozen=True)
class EventWindowPolicy:
    lookback: timedelta
    lookahead: timedelta
    include_unknown_severity: bool = False

    def __post_init__(self) -> None:
        if self.lookback < timedelta(0) or self.lookahead < timedelta(0):
            raise ValueError("event windows must be non-negative")


@dataclass(frozen=True)
class AbnormalityObservation:
    timestamp: datetime
    realized_range_ratio: float | None = None
    volume_ratio: float | None = None
    spread_ratio: float | None = None
    gap_ratio: float | None = None


@dataclass(frozen=True)
class EventContext:
    as_of: datetime
    events: Sequence[MarketEvent]
    highest_severity: EventSeverity
    surprise_magnitude: float | None
    abnormality_score: float | None
    fingerprint: str
    provenance: Mapping[str, str]


_SEVERITY_RANK = {
    EventSeverity.UNKNOWN: 0,
    EventSeverity.LOW: 1,
    EventSeverity.MEDIUM: 2,
    EventSeverity.HIGH: 3,
    EventSeverity.EXTREME: 4,
}


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


def normalize_events(events: Iterable[MarketEvent]) -> tuple[MarketEvent, ...]:
    normalized: list[MarketEvent] = []
    for event in events:
        _require_aware(event.timestamp, "MarketEvent.timestamp")
        normalized.append(event)
    return tuple(sorted(normalized, key=lambda e: (e.timestamp, e.event_id)))


def select_event_window(
    events: Iterable[MarketEvent],
    *,
    as_of: datetime,
    policy: EventWindowPolicy,
) -> tuple[MarketEvent, ...]:
    _require_aware(as_of, "as_of")
    lower = as_of - policy.lookback
    upper = as_of + policy.lookahead
    selected = []
    for event in normalize_events(events):
        if event.timestamp < lower or event.timestamp > upper:
            continue
        if event.severity is EventSeverity.UNKNOWN and not policy.include_unknown_severity:
            continue
        selected.append(event)
    return tuple(selected)


def highest_severity(events: Sequence[MarketEvent]) -> EventSeverity:
    if not events:
        return EventSeverity.UNKNOWN
    return max((event.severity for event in events), key=lambda severity: _SEVERITY_RANK[severity])


def aggregate_surprise(events: Sequence[MarketEvent]) -> float | None:
    values = [abs(float(event.surprise)) for event in events if event.surprise is not None]
    if not values:
        return None
    return max(values)


def abnormality_score(observation: AbnormalityObservation | None) -> float | None:
    if observation is None:
        return None
    components = [
        observation.realized_range_ratio,
        observation.volume_ratio,
        observation.spread_ratio,
        observation.gap_ratio,
    ]
    finite = [max(0.0, float(value)) for value in components if value is not None]
    if not finite:
        return None
    return sum(finite) / len(finite)


def event_fingerprint(events: Sequence[MarketEvent]) -> str:
    payload = "\n".join(
        "|".join(
            (
                event.event_id,
                event.event_type,
                event.timestamp.isoformat(),
                event.severity.value,
                event.source,
                "" if event.surprise is None else repr(float(event.surprise)),
            )
        )
        for event in events
    )
    return sha256(payload.encode("utf-8")).hexdigest()


class EventContextBuilder:
    """Builds deterministic, point-in-time event context for research and replay."""

    def __init__(self, policy: EventWindowPolicy, version: str = "1.0") -> None:
        self.policy = policy
        self.version = version

    def build(
        self,
        events: Iterable[MarketEvent],
        *,
        as_of: datetime,
        observation: AbnormalityObservation | None = None,
    ) -> EventContext:
        selected = select_event_window(events, as_of=as_of, policy=self.policy)
        return EventContext(
            as_of=as_of,
            events=selected,
            highest_severity=highest_severity(selected),
            surprise_magnitude=aggregate_surprise(selected),
            abnormality_score=abnormality_score(observation),
            fingerprint=event_fingerprint(selected),
            provenance={"event_context_version": self.version},
        )
