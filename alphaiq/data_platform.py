from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Mapping, Protocol, Sequence

from .domain import MarketSnapshot


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper().replace(" ", "")
    if not value:
        raise ValueError("symbol is required")
    return value


def normalize_timeframe(timeframe: str) -> str:
    value = timeframe.strip().upper()
    if not value:
        raise ValueError("timeframe is required")
    return value


@dataclass(frozen=True)
class DataQualityPolicy:
    max_age: timedelta
    reject_future_observations: bool = True
    require_monotonic_time: bool = True

    def __post_init__(self) -> None:
        if self.max_age.total_seconds() <= 0:
            raise ValueError("max_age must be positive")


@dataclass(frozen=True)
class DataQualityReport:
    valid: bool
    reasons: tuple[str, ...] = ()
    newest_timestamp: datetime | None = None
    oldest_timestamp: datetime | None = None
    observation_count: int = 0


class SnapshotStore(Protocol):
    def append(self, snapshot: MarketSnapshot) -> None: ...

    def read(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[MarketSnapshot]: ...


@dataclass
class InMemorySnapshotStore:
    _items: list[MarketSnapshot] = field(default_factory=list)

    def append(self, snapshot: MarketSnapshot) -> None:
        self._items.append(snapshot)

    def read(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[MarketSnapshot]:
        _require_aware(start, "start")
        _require_aware(end, "end")
        ns = normalize_symbol(symbol)
        nt = normalize_timeframe(timeframe)
        return tuple(
            item
            for item in sorted(self._items, key=lambda x: x.timestamp)
            if normalize_symbol(item.symbol) == ns
            and normalize_timeframe(item.timeframe) == nt
            and start <= item.timestamp <= end
        )


def validate_point_in_time(
    snapshots: Iterable[MarketSnapshot],
    *,
    as_of: datetime,
    policy: DataQualityPolicy,
) -> DataQualityReport:
    _require_aware(as_of, "as_of")
    ordered = tuple(snapshots)
    if not ordered:
        return DataQualityReport(valid=False, reasons=("no_observations",))

    reasons: list[str] = []
    times = [item.timestamp for item in ordered]

    if policy.reject_future_observations and any(ts > as_of for ts in times):
        reasons.append("future_observation")

    if policy.require_monotonic_time and any(b < a for a, b in zip(times, times[1:])):
        reasons.append("non_monotonic_time")

    newest = max(times)
    oldest = min(times)
    if as_of - newest > policy.max_age:
        reasons.append("stale_data")

    return DataQualityReport(
        valid=not reasons,
        reasons=tuple(reasons),
        newest_timestamp=newest,
        oldest_timestamp=oldest,
        observation_count=len(ordered),
    )


def provenance_for_snapshot(snapshot: MarketSnapshot) -> Mapping[str, str]:
    return {
        "symbol": normalize_symbol(snapshot.symbol),
        "timeframe": normalize_timeframe(snapshot.timeframe),
        "timestamp": snapshot.timestamp.isoformat(),
        "source": snapshot.source,
    }
