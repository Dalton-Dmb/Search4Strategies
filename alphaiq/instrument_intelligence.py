"""Multi-instrument empirical intelligence for AlphaIQ™.

This module is research/validation only. It does not submit orders. It keeps
instrument identity independent from broker symbol conventions and builds a
multi-dimensional empirical map so AlphaIQ™ can learn which strategy engines
are strongest on which instruments, regimes and timeframe combinations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from statistics import fmean, pstdev
from typing import Iterable, Mapping, Sequence

from .validation import ResearchObservation, calculate_metrics


@dataclass(frozen=True, slots=True)
class InstrumentSpec:
    canonical_symbol: str
    asset_class: str
    priority: int
    broker_aliases: Mapping[str, str] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.canonical_symbol or not self.asset_class:
            raise ValueError("canonical_symbol and asset_class are required")
        if self.priority < 0:
            raise ValueError("priority must be non-negative")

    def symbol_for_broker(self, broker: str) -> str:
        """Return a configured broker alias, otherwise the canonical symbol."""
        return self.broker_aliases.get(broker, self.canonical_symbol)


@dataclass(frozen=True, slots=True)
class InstrumentUniverse:
    version: str
    instruments: tuple[InstrumentSpec, ...]
    thesis_timeframes: tuple[str, ...] = ("H4", "H1")
    entry_timeframes: tuple[str, ...] = ("H1", "M30", "M15", "M5")

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("universe version is required")
        symbols = [item.canonical_symbol for item in self.instruments]
        if len(symbols) != len(set(symbols)):
            raise ValueError("canonical symbols must be unique")
        if not self.thesis_timeframes or not self.entry_timeframes:
            raise ValueError("timeframe sets cannot be empty")

    def enabled_symbols(self) -> tuple[str, ...]:
        ordered = sorted(
            (item for item in self.instruments if item.enabled),
            key=lambda item: (-item.priority, item.canonical_symbol),
        )
        return tuple(item.canonical_symbol for item in ordered)

    def get(self, canonical_symbol: str) -> InstrumentSpec:
        for item in self.instruments:
            if item.canonical_symbol == canonical_symbol:
                return item
        raise KeyError(canonical_symbol)


def default_research_universe(version: str = "u1") -> InstrumentUniverse:
    """Reference universe, deliberately Gold-prioritised but not Gold-only.

    Broker aliases are intentionally left configuration-driven because naming
    conventions differ across venues/accounts. More instruments can be added
    without changing strategy code.
    """
    specs = (
        InstrumentSpec("XAUUSD", "METAL", 100, tags=("gold", "priority")),
        InstrumentSpec("XAUGBP", "METAL", 98, tags=("gold", "priority")),
        InstrumentSpec("XAUEUR", "METAL", 96, tags=("gold", "priority")),
        InstrumentSpec("XAUJPY", "METAL", 94, tags=("gold", "priority")),
        InstrumentSpec("XAGUSD", "METAL", 80, tags=("silver",)),
        InstrumentSpec("USDJPY", "FX", 90),
        InstrumentSpec("USDCHF", "FX", 88),
        InstrumentSpec("EURCHF", "FX", 87),
        InstrumentSpec("EURUSD", "FX", 86),
        InstrumentSpec("GBPUSD", "FX", 85),
        InstrumentSpec("NZDUSD", "FX", 84),
        InstrumentSpec("AUDUSD", "FX", 83),
        InstrumentSpec("USDCAD", "FX", 82),
        InstrumentSpec("GBPJPY", "FX", 81),
        InstrumentSpec("EURJPY", "FX", 79),
        InstrumentSpec("EURGBP", "FX", 78),
        InstrumentSpec("GBPCHF", "FX", 77),
        InstrumentSpec("AUDJPY", "FX", 76),
        InstrumentSpec("CADJPY", "FX", 75),
    )
    return InstrumentUniverse(version=version, instruments=specs)


@dataclass(frozen=True, slots=True)
class EmpiricalObservation:
    """Research observation enriched with path/execution/timeframe evidence."""

    research: ResearchObservation
    thesis_timeframe: str
    entry_timeframe: str
    session: str = "unspecified"
    event_state: str = "normal"
    broker: str = "unspecified"
    mfe_r: float | None = None
    mae_r: float | None = None
    slippage_r: float | None = None
    latency_ms: float | None = None

    def __post_init__(self) -> None:
        if not self.thesis_timeframe or not self.entry_timeframe:
            raise ValueError("thesis and entry timeframes are required")
        if self.mfe_r is not None and self.mfe_r < 0:
            raise ValueError("mfe_r is a non-negative excursion magnitude")
        if self.mae_r is not None and self.mae_r < 0:
            raise ValueError("mae_r is a non-negative excursion magnitude")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")


@dataclass(frozen=True, slots=True)
class EmpiricalMapPolicy:
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
class RankingWeights:
    """Explicit research ranking weights; no hidden strategy preference."""

    conservative_expectancy: float
    sharpe_like: float
    sortino_like: float
    profit_factor: float
    drawdown_penalty: float
    slippage_penalty: float

    def __post_init__(self) -> None:
        values = (
            self.conservative_expectancy,
            self.sharpe_like,
            self.sortino_like,
            self.profit_factor,
            self.drawdown_penalty,
            self.slippage_penalty,
        )
        if any(value < 0 for value in values):
            raise ValueError("ranking weights must be non-negative")
        if not any(value > 0 for value in values):
            raise ValueError("at least one ranking weight must be positive")


@dataclass(frozen=True, slots=True)
class EmpiricalCell:
    symbol: str
    regime: str
    strategy_id: str
    strategy_version: str
    thesis_timeframe: str
    entry_timeframe: str
    session: str
    event_state: str
    fold: str
    sample_size: int
    expectancy_r: float | None
    lower_expectancy_r: float | None
    upper_expectancy_r: float | None
    win_rate: float | None
    payoff_ratio: float | None
    profit_factor: float | None
    max_drawdown_r: float | None
    sharpe_like: float | None
    sortino_like: float | None
    average_mfe_r: float | None
    average_mae_r: float | None
    capture_efficiency: float | None
    average_slippage_r: float | None
    average_latency_ms: float | None
    eligible_for_inference: bool
    reason: str


@dataclass(frozen=True, slots=True)
class EngineInstrumentScore:
    strategy_id: str
    strategy_version: str
    symbol: str
    supported_cells: int
    sample_size: int
    weighted_lower_expectancy_r: float
    weighted_sharpe_like: float
    weighted_sortino_like: float
    weighted_profit_factor: float
    weighted_max_drawdown_r: float
    weighted_slippage_r: float
    productivity_score: float


def _interval(values: Sequence[float], z: float) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    mean = fmean(values)
    if len(values) < 2:
        return mean, mean
    sigma = pstdev(values)
    half_width = z * sigma / sqrt(len(values))
    return mean - half_width, mean + half_width


def _sortino_like(values: Sequence[float]) -> float | None:
    if not values:
        return None
    mean = fmean(values)
    downside = [min(value, 0.0) for value in values]
    downside_deviation = sqrt(sum(value * value for value in downside) / len(values))
    if downside_deviation == 0:
        return None
    return mean / downside_deviation * sqrt(len(values))


def _mean_optional(values: Iterable[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return fmean(present) if present else None


def _capture_efficiency(observations: Sequence[EmpiricalObservation]) -> float | None:
    ratios = [
        max(obs.research.outcome_r, 0.0) / obs.mfe_r
        for obs in observations
        if obs.mfe_r is not None and obs.mfe_r > 0 and obs.research.outcome_r > 0
    ]
    return fmean(ratios) if ratios else None


def build_empirical_map(
    observations: Iterable[EmpiricalObservation],
    policy: EmpiricalMapPolicy,
) -> Mapping[tuple[str, str, str, str, str, str, str, str, str], EmpiricalCell]:
    grouped: dict[
        tuple[str, str, str, str, str, str, str, str, str],
        list[EmpiricalObservation],
    ] = {}
    for obs in observations:
        r = obs.research
        key = (
            r.symbol,
            r.regime,
            r.strategy_id,
            r.strategy_version,
            obs.thesis_timeframe,
            obs.entry_timeframe,
            obs.session,
            obs.event_state,
            r.fold,
        )
        grouped.setdefault(key, []).append(obs)

    result: dict[tuple[str, str, str, str, str, str, str, str, str], EmpiricalCell] = {}
    for key in sorted(grouped):
        group = grouped[key]
        outcomes = [obs.research.outcome_r for obs in group]
        metrics = calculate_metrics(outcomes)
        lo, hi = _interval(outcomes, policy.confidence_z)
        sufficient = len(group) >= policy.minimum_sample_size
        symbol, regime, strategy_id, strategy_version, thesis_tf, entry_tf, session, event_state, fold = key
        result[key] = EmpiricalCell(
            symbol=symbol,
            regime=regime,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            thesis_timeframe=thesis_tf,
            entry_timeframe=entry_tf,
            session=session,
            event_state=event_state,
            fold=fold,
            sample_size=len(group),
            expectancy_r=metrics.expectancy_r,
            lower_expectancy_r=lo,
            upper_expectancy_r=hi,
            win_rate=metrics.win_rate,
            payoff_ratio=metrics.payoff_ratio,
            profit_factor=metrics.profit_factor,
            max_drawdown_r=metrics.max_drawdown_r,
            sharpe_like=metrics.sharpe_like,
            sortino_like=_sortino_like(outcomes),
            average_mfe_r=_mean_optional(obs.mfe_r for obs in group),
            average_mae_r=_mean_optional(obs.mae_r for obs in group),
            capture_efficiency=_capture_efficiency(group),
            average_slippage_r=_mean_optional(obs.slippage_r for obs in group),
            average_latency_ms=_mean_optional(obs.latency_ms for obs in group),
            eligible_for_inference=sufficient,
            reason="sufficient research sample" if sufficient else "insufficient research sample",
        )
    return result


def rank_engine_instruments(
    matrix: Mapping[tuple[str, str, str, str, str, str, str, str, str], EmpiricalCell],
    weights: RankingWeights,
) -> Mapping[tuple[str, str], tuple[EngineInstrumentScore, ...]]:
    """Rank instruments independently for every strategy/version.

    Only adequately sampled cells are used. Fold separation remains intact in
    the empirical map; callers should normally pass only the intended OOS fold
    when producing an OOS leaderboard.
    """
    grouped: dict[tuple[str, str, str], list[EmpiricalCell]] = {}
    for cell in matrix.values():
        if not cell.eligible_for_inference or cell.lower_expectancy_r is None:
            continue
        grouped.setdefault((cell.strategy_id, cell.strategy_version, cell.symbol), []).append(cell)

    by_engine: dict[tuple[str, str], list[EngineInstrumentScore]] = {}
    for (strategy_id, strategy_version, symbol), cells in sorted(grouped.items()):
        total = sum(cell.sample_size for cell in cells)
        if total <= 0:
            continue

        def weighted(metric: str, missing: float = 0.0) -> float:
            return sum((getattr(cell, metric) if getattr(cell, metric) is not None else missing) * cell.sample_size for cell in cells) / total

        lower = weighted("lower_expectancy_r")
        sharpe = weighted("sharpe_like")
        sortino = weighted("sortino_like")
        pf = weighted("profit_factor")
        drawdown = weighted("max_drawdown_r")
        slippage = weighted("average_slippage_r")
        score = (
            weights.conservative_expectancy * lower
            + weights.sharpe_like * sharpe
            + weights.sortino_like * sortino
            + weights.profit_factor * pf
            - weights.drawdown_penalty * drawdown
            - weights.slippage_penalty * abs(slippage)
        )
        row = EngineInstrumentScore(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            symbol=symbol,
            supported_cells=len(cells),
            sample_size=total,
            weighted_lower_expectancy_r=lower,
            weighted_sharpe_like=sharpe,
            weighted_sortino_like=sortino,
            weighted_profit_factor=pf,
            weighted_max_drawdown_r=drawdown,
            weighted_slippage_r=slippage,
            productivity_score=score,
        )
        by_engine.setdefault((strategy_id, strategy_version), []).append(row)

    return {
        engine: tuple(sorted(rows, key=lambda row: (-row.productivity_score, -row.sample_size, row.symbol)))
        for engine, rows in sorted(by_engine.items())
    }
