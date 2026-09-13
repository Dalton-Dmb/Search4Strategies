"""Reproducible regime × strategy research matrix for AlphaIQ™.

This module summarizes already-observed research outcomes. It does not create
signals or submit orders.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import fmean, pstdev
from typing import Iterable, Mapping

from .validation import ResearchObservation, calculate_metrics


@dataclass(frozen=True, slots=True)
class MatrixPolicy:
    version: str
    minimum_sample_size: int = 30
    confidence_z: float = 1.96

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("policy version is required")
        if self.minimum_sample_size < 1:
            raise ValueError("minimum_sample_size must be positive")
        if self.confidence_z <= 0:
            raise ValueError("confidence_z must be positive")


@dataclass(frozen=True, slots=True)
class MatrixCell:
    regime: str
    strategy_id: str
    strategy_version: str
    fold: str
    sample_size: int
    expectancy_r: float | None
    lower_expectancy_r: float | None
    upper_expectancy_r: float | None
    win_rate: float | None
    profit_factor: float | None
    max_drawdown_r: float | None
    eligible_for_inference: bool
    reason: str


def _expectancy_interval(values: list[float], z: float) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    mean = fmean(values)
    if len(values) < 2:
        return mean, mean
    sigma = pstdev(values)
    half_width = z * sigma / sqrt(len(values))
    return mean - half_width, mean + half_width


def build_performance_matrix(
    observations: Iterable[ResearchObservation],
    policy: MatrixPolicy,
) -> Mapping[tuple[str, str, str, str], MatrixCell]:
    grouped: dict[tuple[str, str, str, str], list[float]] = {}
    for obs in observations:
        key = (obs.regime, obs.strategy_id, obs.strategy_version, obs.fold)
        grouped.setdefault(key, []).append(obs.outcome_r)

    result: dict[tuple[str, str, str, str], MatrixCell] = {}
    for key in sorted(grouped):
        values = grouped[key]
        metrics = calculate_metrics(values)
        lo, hi = _expectancy_interval(values, policy.confidence_z)
        sufficient = len(values) >= policy.minimum_sample_size
        reason = "sufficient research sample" if sufficient else "insufficient research sample"
        regime, strategy_id, strategy_version, fold = key
        result[key] = MatrixCell(
            regime=regime,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            fold=fold,
            sample_size=len(values),
            expectancy_r=metrics.expectancy_r,
            lower_expectancy_r=lo,
            upper_expectancy_r=hi,
            win_rate=metrics.win_rate,
            profit_factor=metrics.profit_factor,
            max_drawdown_r=metrics.max_drawdown_r,
            eligible_for_inference=sufficient,
            reason=reason,
        )
    return result


def rank_supported_cells(
    matrix: Mapping[tuple[str, str, str, str], MatrixCell],
) -> list[MatrixCell]:
    """Rank only adequately sampled cells by conservative expectancy.

    The lower confidence bound is used to discourage headline ranking from
    rewarding noisy small samples. Cells without sufficient evidence are
    intentionally excluded rather than assigned a favourable score.
    """
    supported = [
        cell for cell in matrix.values()
        if cell.eligible_for_inference and cell.lower_expectancy_r is not None
    ]
    return sorted(
        supported,
        key=lambda c: (
            -(c.lower_expectancy_r or float("-inf")),
            -c.sample_size,
            c.regime,
            c.strategy_id,
            c.strategy_version,
            c.fold,
        ),
    )
