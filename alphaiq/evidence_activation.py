"""Empirical evidence activation contracts for AlphaIQ™.

Research/replay only. This module connects external historical bar providers to the
validated historical-data layer without coupling AlphaIQ™ to a vendor. It also
constructs point-in-time multi-timeframe snapshots: only bars closed at or before
the decision timestamp are visible, preventing higher-timeframe look-ahead.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping, Protocol, Sequence

from .historical_data import HistoricalBar, canonicalize_symbol
from .instrument_intelligence import InstrumentUniverse

_TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}


@dataclass(frozen=True, slots=True)
class HistoricalRequest:
    canonical_symbol: str
    timeframe: str
    start_at: datetime
    end_at: datetime

    def __post_init__(self) -> None:
        if self.timeframe not in _TIMEFRAME_MINUTES:
            raise ValueError(f"unsupported timeframe: {self.timeframe}")
        if any(v.tzinfo is None or v.utcoffset() is None for v in (self.start_at, self.end_at)):
            raise ValueError("request timestamps must be timezone-aware")
        if self.end_at <= self.start_at:
            raise ValueError("end_at must follow start_at")
        if not self.canonical_symbol:
            raise ValueError("canonical_symbol is required")


@dataclass(frozen=True, slots=True)
class ProviderBar:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class HistoricalBarProvider(Protocol):
    provider_id: str
    broker_id: str | None

    def fetch_bars(self, request: HistoricalRequest) -> Sequence[ProviderBar]: ...


@dataclass(frozen=True, slots=True)
class PointInTimeSnapshot:
    symbol: str
    as_of: datetime
    bars: Mapping[str, tuple[HistoricalBar, ...]]

    def latest(self, timeframe: str) -> HistoricalBar | None:
        values = self.bars.get(timeframe, ())
        return values[-1] if values else None


def normalize_provider_bars(
    provider: HistoricalBarProvider,
    request: HistoricalRequest,
    bars: Sequence[ProviderBar],
    universe: InstrumentUniverse,
) -> tuple[HistoricalBar, ...]:
    """Normalize provider output into canonical AlphaIQ™ historical bars.

    The provider may return broker aliases, but every result must resolve to the
    requested canonical instrument. Out-of-range timestamps are rejected rather
    than silently truncated so provider defects remain auditable.
    """
    normalized: list[HistoricalBar] = []
    for bar in bars:
        if bar.timestamp.tzinfo is None or bar.timestamp.utcoffset() is None:
            raise ValueError("provider bar timestamp must be timezone-aware")
        if not request.start_at <= bar.timestamp < request.end_at:
            raise ValueError("provider returned bar outside requested interval")
        canonical = canonicalize_symbol(bar.symbol, universe, provider.broker_id)
        if canonical != request.canonical_symbol:
            raise ValueError("provider returned a different canonical instrument")
        normalized.append(
            HistoricalBar(
                timestamp=bar.timestamp.astimezone(timezone.utc),
                symbol=canonical,
                timeframe=request.timeframe,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                source=provider.provider_id,
                source_symbol=bar.symbol,
            )
        )
    return tuple(normalized)


def ingest_request(
    provider: HistoricalBarProvider,
    request: HistoricalRequest,
    universe: InstrumentUniverse,
) -> tuple[HistoricalBar, ...]:
    return normalize_provider_bars(provider, request, provider.fetch_bars(request), universe)


def closed_at(bar: HistoricalBar) -> datetime:
    return bar.timestamp.astimezone(timezone.utc) + timedelta(minutes=_TIMEFRAME_MINUTES[bar.timeframe])


def build_point_in_time_snapshot(
    bars: Sequence[HistoricalBar],
    symbol: str,
    as_of: datetime,
    history_limit: int | None = None,
) -> PointInTimeSnapshot:
    """Return only observations that were fully closed by ``as_of``.

    This is the key multi-timeframe anti-look-ahead boundary. For example an H1
    bar timestamped 10:00 is not visible at 10:15 because it closes at 11:00.
    """
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    if history_limit is not None and history_limit < 1:
        raise ValueError("history_limit must be positive")
    cutoff = as_of.astimezone(timezone.utc)
    grouped: dict[str, list[HistoricalBar]] = {}
    for bar in bars:
        if bar.symbol != symbol or closed_at(bar) > cutoff:
            continue
        grouped.setdefault(bar.timeframe, []).append(bar)
    result: dict[str, tuple[HistoricalBar, ...]] = {}
    for timeframe, values in grouped.items():
        ordered = sorted(values, key=lambda value: value.timestamp)
        if history_limit is not None:
            ordered = ordered[-history_limit:]
        result[timeframe] = tuple(ordered)
    return PointInTimeSnapshot(symbol=symbol, as_of=as_of, bars=result)


def build_research_requests(
    universe: InstrumentUniverse,
    timeframes: Sequence[str],
    start_at: datetime,
    end_at: datetime,
) -> tuple[HistoricalRequest, ...]:
    """Build deterministic Gold-priority/multi-asset requests from the universe."""
    requests = []
    for symbol in universe.enabled_symbols():
        for timeframe in timeframes:
            requests.append(HistoricalRequest(symbol, timeframe, start_at, end_at))
    return tuple(requests)
