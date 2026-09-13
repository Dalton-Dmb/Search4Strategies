"""Deterministic research validation contracts for AlphaIQ™.

This module is intentionally research/backtest only. It records reproducible
observations and evaluates aggregate evidence without submitting orders.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import sqrt
from statistics import fmean, pstdev
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ResearchObservation:
    """One point-in-time strategy outcome used by the validation harness."""

    as_of: datetime
    symbol: str
    timeframe: str
    regime: str
    strategy_id: str
    strategy_version: str
    outcome_r: float
    feature_fingerprint: str
    configuration_version: str
    fold: str = "unspecified"
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if not self.symbol or not self.timeframe or not self.regime:
            raise ValueError("symbol, timeframe and regime are required")
        if not self.strategy_id or not self.strategy_version:
            raise ValueError("strategy identity and version are required")
        if not self.feature_fingerprint or not self.configuration_version:
            raise ValueError("feature/configuration lineage is required")

    def canonical(self) -> dict[str, object]:
        return {
            "as_of": self.as_of.astimezone(timezone.utc).isoformat(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "regime": self.regime,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "outcome_r": self.outcome_r,
            "feature_fingerprint": self.feature_fingerprint,
            "configuration_version": self.configuration_version,
            "fold": self.fold,
            "metadata": dict(sorted(self.metadata.items())),
        }


@dataclass(frozen=True, slots=True)
class ValidationRunManifest:
    run_id: str
    created_at: datetime
    dataset_fingerprint: str
    feature_fingerprint: str
    configuration_version: str
    code_version: str

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if not all((self.run_id, self.dataset_fingerprint, self.feature_fingerprint,
                    self.configuration_version, self.code_version)):
            raise ValueError("complete run lineage is required")


@dataclass(frozen=True, slots=True)
class ResearchMetrics:
    count: int
    expectancy_r: float | None
    win_rate: float | None
    payoff_ratio: float | None
    profit_factor: float | None
    max_drawdown_r: float | None
    sharpe_like: float | None


def deterministic_observation_fingerprint(observations: Iterable[ResearchObservation]) -> str:
    ordered = sorted(
        (o.canonical() for o in observations),
        key=lambda x: (x["as_of"], x["symbol"], x["timeframe"], x["strategy_id"], x["strategy_version"]),
    )
    payload = json.dumps(ordered, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()


def assert_chronological(observations: Sequence[ResearchObservation]) -> None:
    timestamps = [o.as_of for o in observations]
    if timestamps != sorted(timestamps):
        raise ValueError("research observations must be chronological")


def assert_point_in_time(observations: Iterable[ResearchObservation], cutoff: datetime) -> None:
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("cutoff must be timezone-aware")
    future = [o for o in observations if o.as_of > cutoff]
    if future:
        raise ValueError("future observations detected")


def calculate_metrics(outcomes_r: Sequence[float]) -> ResearchMetrics:
    if not outcomes_r:
        return ResearchMetrics(0, None, None, None, None, None, None)

    positives = [x for x in outcomes_r if x > 0]
    negatives = [x for x in outcomes_r if x < 0]
    expectancy = fmean(outcomes_r)
    win_rate = len(positives) / len(outcomes_r)
    avg_win = fmean(positives) if positives else None
    avg_loss = abs(fmean(negatives)) if negatives else None
    payoff = (avg_win / avg_loss) if avg_win is not None and avg_loss not in (None, 0.0) else None
    gross_win = sum(positives)
    gross_loss = abs(sum(negatives))
    profit_factor = gross_win / gross_loss if gross_loss > 0 else None

    equity = peak = 0.0
    max_dd = 0.0
    for result in outcomes_r:
        equity += result
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    sigma = pstdev(outcomes_r) if len(outcomes_r) > 1 else 0.0
    sharpe_like = expectancy / sigma * sqrt(len(outcomes_r)) if sigma > 0 else None
    return ResearchMetrics(len(outcomes_r), expectancy, win_rate, payoff, profit_factor, max_dd, sharpe_like)


def group_metrics(
    observations: Iterable[ResearchObservation],
) -> dict[tuple[str, str, str], ResearchMetrics]:
    grouped: dict[tuple[str, str, str], list[float]] = {}
    for obs in observations:
        key = (obs.regime, obs.strategy_id, obs.strategy_version)
        grouped.setdefault(key, []).append(obs.outcome_r)
    return {key: calculate_metrics(values) for key, values in sorted(grouped.items())}
