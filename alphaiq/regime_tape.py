"""Historical regime-tape construction for AlphaIQ™ empirical research.

The tape is generated strictly from point-in-time snapshots and an explicit
evidence extractor. No hidden thresholds or forward-looking bars are introduced.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence

from .evidence_activation import PointInTimeSnapshot, build_point_in_time_snapshot
from .historical_data import HistoricalBar
from .regime_labelling import OperationalRegime, RegimeEvidence, RegimeThresholds, label_regime


class RegimeEvidenceExtractor(Protocol):
    version: str

    def extract(self, snapshot: PointInTimeSnapshot) -> RegimeEvidence: ...


@dataclass(frozen=True, slots=True)
class RegimeTapePoint:
    symbol: str
    as_of: datetime
    regime: OperationalRegime
    confidence: float
    threshold_version: str
    evidence_version: str
    reason: str


@dataclass(frozen=True, slots=True)
class RegimeTape:
    symbol: str
    decision_timeframe: str
    points: tuple[RegimeTapePoint, ...]


def decision_timestamps(
    bars: Sequence[HistoricalBar],
    symbol: str,
    decision_timeframe: str,
) -> tuple[datetime, ...]:
    """Use the close time of each decision-timeframe bar as a replay decision point."""
    from .evidence_activation import closed_at

    values = {
        closed_at(bar)
        for bar in bars
        if bar.symbol == symbol and bar.timeframe == decision_timeframe
    }
    return tuple(sorted(values))


def build_regime_tape(
    bars: Sequence[HistoricalBar],
    symbol: str,
    decision_timeframe: str,
    extractor: RegimeEvidenceExtractor,
    thresholds: RegimeThresholds,
    history_limit: int | None = None,
) -> RegimeTape:
    """Classify each historical decision timestamp without future-bar access."""
    points: list[RegimeTapePoint] = []
    for as_of in decision_timestamps(bars, symbol, decision_timeframe):
        snapshot = build_point_in_time_snapshot(bars, symbol, as_of, history_limit)
        evidence = extractor.extract(snapshot)
        result = label_regime(evidence, thresholds)
        points.append(
            RegimeTapePoint(
                symbol=symbol,
                as_of=as_of,
                regime=result.regime,
                confidence=result.confidence,
                threshold_version=result.threshold_version,
                evidence_version=extractor.version,
                reason=result.reason,
            )
        )
    return RegimeTape(symbol=symbol, decision_timeframe=decision_timeframe, points=tuple(points))
