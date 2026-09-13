from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence

from .domain import JournalEvent


@dataclass(frozen=True)
class DecisionTrace:
    correlation_id: str
    events: Sequence[JournalEvent]

    def __post_init__(self) -> None:
        if not self.correlation_id:
            raise ValueError("correlation_id is required")
        if any(event.correlation_id != self.correlation_id for event in self.events):
            raise ValueError("all events must share the trace correlation_id")

    @property
    def started_at(self) -> datetime | None:
        if not self.events:
            return None
        return min(event.timestamp for event in self.events)

    @property
    def ended_at(self) -> datetime | None:
        if not self.events:
            return None
        return max(event.timestamp for event in self.events)

    def event_types(self) -> tuple[str, ...]:
        return tuple(event.event_type for event in sorted(self.events, key=lambda e: e.timestamp))

    def fingerprint(self) -> str:
        ordered = sorted(self.events, key=lambda e: (e.timestamp, e.event_id))
        payload = "\n".join(
            "|".join(
                (
                    event.event_id,
                    event.event_type,
                    event.timestamp.isoformat(),
                    event.schema_version,
                    repr(sorted(event.payload.items())),
                )
            )
            for event in ordered
        )
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TraceSummary:
    correlation_id: str
    event_count: int
    event_types: Sequence[str]
    started_at: datetime | None
    ended_at: datetime | None
    fingerprint: str


class TraceIndex:
    """In-memory trace reconstruction index for research and audit workflows."""

    def __init__(self) -> None:
        self._events: list[JournalEvent] = []

    def append(self, event: JournalEvent) -> None:
        self._events.append(event)

    def extend(self, events: Iterable[JournalEvent]) -> None:
        self._events.extend(events)

    def trace(self, correlation_id: str) -> DecisionTrace:
        selected = [event for event in self._events if event.correlation_id == correlation_id]
        selected.sort(key=lambda e: (e.timestamp, e.event_id))
        return DecisionTrace(correlation_id=correlation_id, events=tuple(selected))

    def summaries(self) -> tuple[TraceSummary, ...]:
        ids = sorted({event.correlation_id for event in self._events if event.correlation_id})
        result: list[TraceSummary] = []
        for correlation_id in ids:
            trace = self.trace(correlation_id)
            result.append(
                TraceSummary(
                    correlation_id=correlation_id,
                    event_count=len(trace.events),
                    event_types=trace.event_types(),
                    started_at=trace.started_at,
                    ended_at=trace.ended_at,
                    fingerprint=trace.fingerprint(),
                )
            )
        return tuple(result)


@dataclass(frozen=True)
class OutcomeObservation:
    correlation_id: str
    strategy_id: str
    regime: str
    pnl_r: float | None = None
    mae_r: float | None = None
    mfe_r: float | None = None
    slippage_bps: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AttributionSummary:
    key: str
    sample_size: int
    mean_pnl_r: float | None
    mean_mae_r: float | None
    mean_mfe_r: float | None
    mean_slippage_bps: float | None


def _mean(values: Iterable[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None]
    if not finite:
        return None
    return sum(finite) / len(finite)


class LearningAnalytics:
    """Aggregates research outcomes without mutating strategy or model state."""

    def summarize_by_strategy(self, outcomes: Iterable[OutcomeObservation]) -> tuple[AttributionSummary, ...]:
        groups: dict[str, list[OutcomeObservation]] = {}
        for outcome in outcomes:
            groups.setdefault(outcome.strategy_id, []).append(outcome)
        return tuple(self._summarize(key, groups[key]) for key in sorted(groups))

    def summarize_by_regime(self, outcomes: Iterable[OutcomeObservation]) -> tuple[AttributionSummary, ...]:
        groups: dict[str, list[OutcomeObservation]] = {}
        for outcome in outcomes:
            groups.setdefault(outcome.regime, []).append(outcome)
        return tuple(self._summarize(key, groups[key]) for key in sorted(groups))

    def _summarize(self, key: str, values: Sequence[OutcomeObservation]) -> AttributionSummary:
        return AttributionSummary(
            key=key,
            sample_size=len(values),
            mean_pnl_r=_mean(value.pnl_r for value in values),
            mean_mae_r=_mean(value.mae_r for value in values),
            mean_mfe_r=_mean(value.mfe_r for value in values),
            mean_slippage_bps=_mean(value.slippage_bps for value in values),
        )
