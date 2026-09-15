"""Conservative historical trade-path reconstruction for AlphaIQ™ research.

This module never invents intrabar ordering. If both stop and target are touched
inside the same bar and lower-resolution evidence is unavailable, the outcome is
marked AMBIGUOUS rather than choosing the favourable path.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Sequence

from .historical_data import HistoricalBar


class ResearchSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class PathOutcome(str, Enum):
    TARGET = "TARGET"
    STOP = "STOP"
    EXPIRED = "EXPIRED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class TradePathRequest:
    symbol: str
    side: ResearchSide
    entry_at: datetime
    entry_price: float
    stop_price: float
    target_price: float

    def __post_init__(self) -> None:
        if self.entry_at.tzinfo is None or self.entry_at.utcoffset() is None:
            raise ValueError("entry_at must be timezone-aware")
        if min(self.entry_price, self.stop_price, self.target_price) <= 0:
            raise ValueError("trade prices must be positive")
        if self.side is ResearchSide.LONG and not (self.stop_price < self.entry_price < self.target_price):
            raise ValueError("LONG requires stop < entry < target")
        if self.side is ResearchSide.SHORT and not (self.target_price < self.entry_price < self.stop_price):
            raise ValueError("SHORT requires target < entry < stop")


@dataclass(frozen=True, slots=True)
class TradePathResult:
    outcome: PathOutcome
    outcome_r: float | None
    mfe_r: float
    mae_r: float
    exit_at: datetime | None
    bars_observed: int
    reason: str


def _risk(request: TradePathRequest) -> float:
    return abs(request.entry_price - request.stop_price)


def reconstruct_trade_path(request: TradePathRequest, bars: Sequence[HistoricalBar]) -> TradePathResult:
    risk = _risk(request)
    relevant = sorted(
        (bar for bar in bars if bar.symbol == request.symbol and bar.timestamp >= request.entry_at),
        key=lambda bar: bar.timestamp,
    )
    mfe = 0.0
    mae = 0.0

    for index, bar in enumerate(relevant, start=1):
        if request.side is ResearchSide.LONG:
            mfe = max(mfe, (bar.high - request.entry_price) / risk)
            mae = max(mae, (request.entry_price - bar.low) / risk)
            target_hit = bar.high >= request.target_price
            stop_hit = bar.low <= request.stop_price
            target_r = (request.target_price - request.entry_price) / risk
        else:
            mfe = max(mfe, (request.entry_price - bar.low) / risk)
            mae = max(mae, (bar.high - request.entry_price) / risk)
            target_hit = bar.low <= request.target_price
            stop_hit = bar.high >= request.stop_price
            target_r = (request.entry_price - request.target_price) / risk

        if target_hit and stop_hit:
            return TradePathResult(PathOutcome.AMBIGUOUS, None, mfe, mae, bar.timestamp, index, "stop and target touched in same bar; intrabar order unknown")
        if stop_hit:
            return TradePathResult(PathOutcome.STOP, -1.0, mfe, mae, bar.timestamp, index, "stop touched first on observable bars")
        if target_hit:
            return TradePathResult(PathOutcome.TARGET, target_r, mfe, mae, bar.timestamp, index, "target touched first on observable bars")

    return TradePathResult(PathOutcome.EXPIRED, None, mfe, mae, None, len(relevant), "neither stop nor target observed")
