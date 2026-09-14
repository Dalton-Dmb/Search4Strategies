"""Historical research data contracts for AlphaIQ™.

Research/replay only: no live order submission. The module provides canonical,
point-in-time OHLCV data validation, deterministic dataset fingerprints, fold
assignment and evidence-run lineage for empirical regime/strategy research.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

from .instrument_intelligence import InstrumentUniverse


_TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}


@dataclass(frozen=True, slots=True)
class HistoricalBar:
    timestamp: datetime
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    source: str = "unspecified"
    source_symbol: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        if not self.symbol or not self.timeframe or not self.source:
            raise ValueError("symbol, timeframe and source are required")
        if self.timeframe not in _TIMEFRAME_MINUTES:
            raise ValueError(f"unsupported timeframe: {self.timeframe}")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC values must be positive")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high is below an OHLC component")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low is above an OHLC component")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume cannot be negative")

    def canonical(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "source": self.source,
            "source_symbol": self.source_symbol,
        }


@dataclass(frozen=True, slots=True)
class DatasetQualityPolicy:
    version: str
    maximum_gap_multiple: float = 3.0
    reject_duplicates: bool = True
    require_strict_chronology: bool = True

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("quality policy version is required")
        if self.maximum_gap_multiple < 1:
            raise ValueError("maximum_gap_multiple must be at least 1")


@dataclass(frozen=True, slots=True)
class DatasetQualityReport:
    valid: bool
    bar_count: int
    duplicate_count: int
    chronology_errors: int
    excessive_gap_count: int
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HistoricalDatasetManifest:
    dataset_id: str
    version: str
    created_at: datetime
    source: str
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...]
    start_at: datetime
    end_at: datetime
    bar_count: int
    fingerprint: str
    quality_policy_version: str

    def __post_init__(self) -> None:
        for value in (self.created_at, self.start_at, self.end_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("manifest timestamps must be timezone-aware")
        if not all((self.dataset_id, self.version, self.source, self.fingerprint, self.quality_policy_version)):
            raise ValueError("complete dataset lineage is required")
        if self.end_at < self.start_at or self.bar_count < 1:
            raise ValueError("invalid manifest range/count")


@dataclass(frozen=True, slots=True)
class FoldBoundary:
    name: str
    start_at: datetime
    end_at: datetime

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("fold name is required")
        if any(v.tzinfo is None or v.utcoffset() is None for v in (self.start_at, self.end_at)):
            raise ValueError("fold timestamps must be timezone-aware")
        if self.end_at <= self.start_at:
            raise ValueError("fold end must follow start")


@dataclass(frozen=True, slots=True)
class EvidenceRunManifest:
    run_id: str
    created_at: datetime
    dataset_fingerprint: str
    feature_fingerprint: str
    regime_policy_version: str
    strategy_catalogue_version: str
    empirical_policy_version: str
    code_version: str
    universe_version: str

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        values = (
            self.run_id, self.dataset_fingerprint, self.feature_fingerprint,
            self.regime_policy_version, self.strategy_catalogue_version,
            self.empirical_policy_version, self.code_version, self.universe_version,
        )
        if not all(values):
            raise ValueError("complete evidence-run lineage is required")

    def fingerprint(self) -> str:
        payload = {
            "run_id": self.run_id,
            "created_at": self.created_at.astimezone(timezone.utc).isoformat(),
            "dataset_fingerprint": self.dataset_fingerprint,
            "feature_fingerprint": self.feature_fingerprint,
            "regime_policy_version": self.regime_policy_version,
            "strategy_catalogue_version": self.strategy_catalogue_version,
            "empirical_policy_version": self.empirical_policy_version,
            "code_version": self.code_version,
            "universe_version": self.universe_version,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def canonicalize_symbol(raw_symbol: str, universe: InstrumentUniverse, broker: str | None = None) -> str:
    raw = raw_symbol.strip().upper()
    for instrument in universe.instruments:
        if raw == instrument.canonical_symbol.upper():
            return instrument.canonical_symbol
        aliases = instrument.broker_aliases
        if broker is not None and aliases.get(broker, "").upper() == raw:
            return instrument.canonical_symbol
        if broker is None and any(alias.upper() == raw for alias in aliases.values()):
            return instrument.canonical_symbol
    raise KeyError(raw_symbol)


def dataset_fingerprint(bars: Iterable[HistoricalBar]) -> str:
    ordered = sorted(
        (bar.canonical() for bar in bars),
        key=lambda x: (x["symbol"], x["timeframe"], x["timestamp"], x["source"]),
    )
    payload = json.dumps(ordered, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()


def validate_dataset(bars: Sequence[HistoricalBar], policy: DatasetQualityPolicy) -> DatasetQualityReport:
    reasons: list[str] = []
    seen: set[tuple[str, str, datetime]] = set()
    duplicates = 0
    chronology_errors = 0
    gaps = 0
    previous: dict[tuple[str, str], datetime] = {}

    for bar in bars:
        key = (bar.symbol, bar.timeframe, bar.timestamp.astimezone(timezone.utc))
        if key in seen:
            duplicates += 1
        seen.add(key)

        series = (bar.symbol, bar.timeframe)
        prev = previous.get(series)
        if prev is not None:
            current = bar.timestamp.astimezone(timezone.utc)
            if current <= prev:
                chronology_errors += 1
            expected = timedelta(minutes=_TIMEFRAME_MINUTES[bar.timeframe])
            if current - prev > expected * policy.maximum_gap_multiple:
                gaps += 1
        previous[series] = bar.timestamp.astimezone(timezone.utc)

    if policy.reject_duplicates and duplicates:
        reasons.append("duplicate bars detected")
    if policy.require_strict_chronology and chronology_errors:
        reasons.append("non-chronological bars detected")
    if gaps:
        reasons.append("excessive gaps detected")
    if not bars:
        reasons.append("dataset is empty")

    return DatasetQualityReport(
        valid=not reasons,
        bar_count=len(bars),
        duplicate_count=duplicates,
        chronology_errors=chronology_errors,
        excessive_gap_count=gaps,
        reasons=tuple(reasons),
    )


def build_dataset_manifest(
    dataset_id: str,
    version: str,
    bars: Sequence[HistoricalBar],
    policy: DatasetQualityPolicy,
    created_at: datetime,
) -> HistoricalDatasetManifest:
    report = validate_dataset(bars, policy)
    if not report.valid:
        raise ValueError("dataset failed quality policy: " + "; ".join(report.reasons))
    ordered = sorted(bars, key=lambda bar: bar.timestamp)
    return HistoricalDatasetManifest(
        dataset_id=dataset_id,
        version=version,
        created_at=created_at,
        source=",".join(sorted({bar.source for bar in bars})),
        symbols=tuple(sorted({bar.symbol for bar in bars})),
        timeframes=tuple(sorted({bar.timeframe for bar in bars})),
        start_at=ordered[0].timestamp,
        end_at=ordered[-1].timestamp,
        bar_count=len(bars),
        fingerprint=dataset_fingerprint(bars),
        quality_policy_version=policy.version,
    )


def validate_fold_boundaries(folds: Sequence[FoldBoundary]) -> None:
    ordered = sorted(folds, key=lambda fold: fold.start_at)
    for previous, current in zip(ordered, ordered[1:]):
        if current.start_at < previous.end_at:
            raise ValueError("research folds overlap")


def assign_fold(timestamp: datetime, folds: Sequence[FoldBoundary]) -> str:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    validate_fold_boundaries(folds)
    matches = [fold.name for fold in folds if fold.start_at <= timestamp < fold.end_at]
    if len(matches) != 1:
        raise ValueError("timestamp must belong to exactly one research fold")
    return matches[0]
