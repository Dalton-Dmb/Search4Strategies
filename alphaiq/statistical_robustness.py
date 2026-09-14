"""Robust empirical statistics for AlphaIQ™ research evidence.

These metrics are for research/validation only. Annualization is explicit through
policy so per-trade and time-normalized Sharpe are never conflated.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from random import Random
from statistics import fmean, pstdev
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class StatisticalPolicy:
    version: str
    periods_per_year: float
    confidence_level: float = 0.95
    bootstrap_samples: int = 1000
    bootstrap_seed: int = 7
    cvar_alpha: float = 0.95
    minimum_sample_size: int = 30

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("statistical policy version is required")
        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        if not 0 < self.confidence_level < 1:
            raise ValueError("confidence_level must be in (0,1)")
        if self.bootstrap_samples < 100:
            raise ValueError("bootstrap_samples must be at least 100")
        if not 0 < self.cvar_alpha < 1:
            raise ValueError("cvar_alpha must be in (0,1)")
        if self.minimum_sample_size < 2:
            raise ValueError("minimum_sample_size must be at least 2")


@dataclass(frozen=True, slots=True)
class ExcursionObservation:
    outcome_r: float
    mfe_r: float | None = None
    mae_r: float | None = None
    time_to_mfe_seconds: float | None = None
    time_to_mae_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.mfe_r is not None and self.mfe_r < 0:
            raise ValueError("mfe_r cannot be negative")
        if self.mae_r is not None and self.mae_r < 0:
            raise ValueError("mae_r cannot be negative")
        if self.time_to_mfe_seconds is not None and self.time_to_mfe_seconds < 0:
            raise ValueError("time_to_mfe_seconds cannot be negative")
        if self.time_to_mae_seconds is not None and self.time_to_mae_seconds < 0:
            raise ValueError("time_to_mae_seconds cannot be negative")


@dataclass(frozen=True, slots=True)
class RobustMetrics:
    sample_size: int
    expectancy_r: float | None
    expectancy_ci: tuple[float, float] | None
    annualized_sharpe: float | None
    annualized_sharpe_ci: tuple[float, float] | None
    annualized_sortino: float | None
    max_drawdown_r: float | None
    calmar_like: float | None
    cvar_r: float | None
    average_mfe_r: float | None
    average_mae_r: float | None
    mfe_mae_ratio: float | None
    capture_efficiency: float | None
    average_time_to_mfe_seconds: float | None
    average_time_to_mae_seconds: float | None
    eligible_for_inference: bool


@dataclass(frozen=True, slots=True)
class DegradationDiagnostic:
    train_metric: float | None
    validation_metric: float | None
    oos_metric: float | None
    oos_vs_train_change: float | None
    oos_vs_validation_change: float | None


def _quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("values required")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = probability * (len(ordered) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    fraction = pos - lo
    return ordered[lo] * (1 - fraction) + ordered[hi] * fraction


def _annualized_sharpe(values: Sequence[float], periods_per_year: float) -> float | None:
    if len(values) < 2:
        return None
    sigma = pstdev(values)
    if sigma == 0:
        return None
    return fmean(values) / sigma * sqrt(periods_per_year)


def _annualized_sortino(values: Sequence[float], periods_per_year: float) -> float | None:
    if not values:
        return None
    downside = [min(value, 0.0) for value in values]
    deviation = sqrt(sum(value * value for value in downside) / len(values))
    if deviation == 0:
        return None
    return fmean(values) / deviation * sqrt(periods_per_year)


def _max_drawdown(values: Sequence[float]) -> float:
    equity = peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def _bootstrap_interval(values: Sequence[float], policy: StatisticalPolicy, statistic) -> tuple[float, float] | None:
    if len(values) < 2:
        return None
    rng = Random(policy.bootstrap_seed)
    estimates: list[float] = []
    n = len(values)
    for _ in range(policy.bootstrap_samples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        estimate = statistic(sample)
        if estimate is not None:
            estimates.append(estimate)
    if not estimates:
        return None
    tail = (1.0 - policy.confidence_level) / 2.0
    return _quantile(estimates, tail), _quantile(estimates, 1.0 - tail)


def _mean_optional(values: Sequence[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return fmean(present) if present else None


def _cvar(values: Sequence[float], alpha: float) -> float | None:
    if not values:
        return None
    loss_tail_probability = 1.0 - alpha
    cutoff = _quantile(values, loss_tail_probability)
    tail = [value for value in values if value <= cutoff]
    return fmean(tail) if tail else cutoff


def calculate_robust_metrics(observations: Sequence[ExcursionObservation], policy: StatisticalPolicy) -> RobustMetrics:
    outcomes = [obs.outcome_r for obs in observations]
    if not outcomes:
        return RobustMetrics(0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, False)

    expectancy = fmean(outcomes)
    sharpe = _annualized_sharpe(outcomes, policy.periods_per_year)
    sortino = _annualized_sortino(outcomes, policy.periods_per_year)
    max_dd = _max_drawdown(outcomes)
    annualized_mean = expectancy * policy.periods_per_year
    calmar = annualized_mean / max_dd if max_dd > 0 else None
    expectancy_ci = _bootstrap_interval(outcomes, policy, lambda sample: fmean(sample))
    sharpe_ci = _bootstrap_interval(outcomes, policy, lambda sample: _annualized_sharpe(sample, policy.periods_per_year))
    avg_mfe = _mean_optional([obs.mfe_r for obs in observations])
    avg_mae = _mean_optional([obs.mae_r for obs in observations])
    mfe_mae = avg_mfe / avg_mae if avg_mfe is not None and avg_mae not in (None, 0.0) else None
    capture_values = [
        max(obs.outcome_r, 0.0) / obs.mfe_r
        for obs in observations
        if obs.mfe_r is not None and obs.mfe_r > 0 and obs.outcome_r > 0
    ]
    capture = fmean(capture_values) if capture_values else None
    return RobustMetrics(
        sample_size=len(outcomes),
        expectancy_r=expectancy,
        expectancy_ci=expectancy_ci,
        annualized_sharpe=sharpe,
        annualized_sharpe_ci=sharpe_ci,
        annualized_sortino=sortino,
        max_drawdown_r=max_dd,
        calmar_like=calmar,
        cvar_r=_cvar(outcomes, policy.cvar_alpha),
        average_mfe_r=avg_mfe,
        average_mae_r=avg_mae,
        mfe_mae_ratio=mfe_mae,
        capture_efficiency=capture,
        average_time_to_mfe_seconds=_mean_optional([obs.time_to_mfe_seconds for obs in observations]),
        average_time_to_mae_seconds=_mean_optional([obs.time_to_mae_seconds for obs in observations]),
        eligible_for_inference=len(outcomes) >= policy.minimum_sample_size,
    )


def degradation_diagnostic(fold_metrics: Mapping[str, float | None]) -> DegradationDiagnostic:
    train = fold_metrics.get("train")
    validation = fold_metrics.get("validation")
    oos = fold_metrics.get("oos")

    def change(base: float | None, current: float | None) -> float | None:
        if base is None or current is None:
            return None
        return current - base

    return DegradationDiagnostic(
        train_metric=train,
        validation_metric=validation,
        oos_metric=oos,
        oos_vs_train_change=change(train, oos),
        oos_vs_validation_change=change(validation, oos),
    )
