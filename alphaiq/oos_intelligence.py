"""Out-of-sample instrument productivity intelligence for AlphaIQ™.

Research/validation only. This module never submits orders. It consumes the
multi-dimensional empirical map and deliberately defaults to OOS evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Mapping

from .instrument_intelligence import EmpiricalCell, RankingWeights
from .strategy_research import ImplementationState, StrategyResearchSpec


@dataclass(frozen=True, slots=True)
class OOSIntelligencePolicy:
    version: str
    oos_fold: str = "OOS"
    minimum_total_samples: int = 30
    minimum_regime_samples: int = 15
    mismatch_floor: float = 1e-9

    def __post_init__(self) -> None:
        if not self.version or not self.oos_fold:
            raise ValueError("policy version and OOS fold are required")
        if self.minimum_total_samples < 1 or self.minimum_regime_samples < 1:
            raise ValueError("sample thresholds must be positive")
        if self.mismatch_floor <= 0:
            raise ValueError("mismatch_floor must be positive")


@dataclass(frozen=True, slots=True)
class RegimeMismatchScore:
    strategy_id: str
    strategy_version: str
    symbol: str
    preferred_regime: str | None
    preferred_expectancy_r: float | None
    outside_expectancy_r: float | None
    degradation_r: float | None
    degradation_ratio: float | None
    preferred_samples: int
    outside_samples: int
    eligible: bool
    reason: str


@dataclass(frozen=True, slots=True)
class OOSProductivityScore:
    strategy_id: str
    strategy_version: str
    symbol: str
    sample_size: int
    supported_cells: int
    conservative_expectancy_r: float
    sharpe_like: float
    sortino_like: float
    profit_factor: float
    max_drawdown_r: float
    slippage_r: float
    productivity_score: float
    mismatch: RegimeMismatchScore


@dataclass(frozen=True, slots=True)
class OOSIntelligenceReport:
    policy_version: str
    fold: str
    rankings_by_engine: Mapping[tuple[str, str], tuple[OOSProductivityScore, ...]]
    best_engine_by_instrument: Mapping[str, OOSProductivityScore]
    fingerprint: str


def _weighted(cells: Iterable[EmpiricalCell], field: str, default: float = 0.0) -> float:
    rows = tuple(cells)
    total = sum(row.sample_size for row in rows)
    if total <= 0:
        return default
    return sum((getattr(row, field) if getattr(row, field) is not None else default) * row.sample_size for row in rows) / total


def _mismatch(cells: tuple[EmpiricalCell, ...], policy: OOSIntelligencePolicy) -> RegimeMismatchScore:
    first = cells[0]
    by_regime: dict[str, list[EmpiricalCell]] = {}
    for cell in cells:
        by_regime.setdefault(cell.regime, []).append(cell)
    eligible_regimes = {
        regime: tuple(rows)
        for regime, rows in by_regime.items()
        if sum(row.sample_size for row in rows) >= policy.minimum_regime_samples
    }
    if not eligible_regimes:
        return RegimeMismatchScore(first.strategy_id, first.strategy_version, first.symbol, None, None, None, None, None, 0, 0, False, "insufficient regime-specific OOS samples")
    preferred = max(eligible_regimes, key=lambda regime: (_weighted(eligible_regimes[regime], "lower_expectancy_r"), regime))
    preferred_rows = eligible_regimes[preferred]
    outside_rows = tuple(row for regime, rows in eligible_regimes.items() if regime != preferred for row in rows)
    preferred_samples = sum(row.sample_size for row in preferred_rows)
    outside_samples = sum(row.sample_size for row in outside_rows)
    preferred_exp = _weighted(preferred_rows, "lower_expectancy_r")
    if not outside_rows:
        return RegimeMismatchScore(first.strategy_id, first.strategy_version, first.symbol, preferred, preferred_exp, None, None, None, preferred_samples, 0, False, "no adequately sampled outside-regime OOS evidence")
    outside_exp = _weighted(outside_rows, "lower_expectancy_r")
    degradation = preferred_exp - outside_exp
    ratio = degradation / max(abs(preferred_exp), policy.mismatch_floor)
    return RegimeMismatchScore(first.strategy_id, first.strategy_version, first.symbol, preferred, preferred_exp, outside_exp, degradation, ratio, preferred_samples, outside_samples, True, "OOS regime mismatch quantified")


def build_oos_intelligence(
    matrix: Mapping[tuple[str, str, str, str, str, str, str, str, str], EmpiricalCell],
    strategy_specs: Iterable[StrategyResearchSpec],
    weights: RankingWeights,
    policy: OOSIntelligencePolicy,
) -> OOSIntelligenceReport:
    """Build a conservative OOS-only leaderboard.

    MANIFEST_ONLY, disabled and unknown strategy versions are excluded. Cells
    from train/validation folds are never mixed into this report.
    """
    certified = {
        (spec.strategy_id, spec.version)
        for spec in strategy_specs
        if spec.implementation_state is ImplementationState.IMPLEMENTED
    }
    grouped: dict[tuple[str, str, str], list[EmpiricalCell]] = {}
    for cell in matrix.values():
        if cell.fold != policy.oos_fold or not cell.eligible_for_inference:
            continue
        if (cell.strategy_id, cell.strategy_version) not in certified:
            continue
        if cell.lower_expectancy_r is None:
            continue
        grouped.setdefault((cell.strategy_id, cell.strategy_version, cell.symbol), []).append(cell)

    by_engine: dict[tuple[str, str], list[OOSProductivityScore]] = {}
    for (strategy_id, version, symbol), raw_cells in sorted(grouped.items()):
        cells = tuple(raw_cells)
        total = sum(cell.sample_size for cell in cells)
        if total < policy.minimum_total_samples:
            continue
        lower = _weighted(cells, "lower_expectancy_r")
        sharpe = _weighted(cells, "sharpe_like")
        sortino = _weighted(cells, "sortino_like")
        pf = _weighted(cells, "profit_factor")
        drawdown = _weighted(cells, "max_drawdown_r")
        slippage = _weighted(cells, "average_slippage_r")
        score = (
            weights.conservative_expectancy * lower
            + weights.sharpe_like * sharpe
            + weights.sortino_like * sortino
            + weights.profit_factor * pf
            - weights.drawdown_penalty * drawdown
            - weights.slippage_penalty * abs(slippage)
        )
        row = OOSProductivityScore(strategy_id, version, symbol, total, len(cells), lower, sharpe, sortino, pf, drawdown, slippage, score, _mismatch(cells, policy))
        by_engine.setdefault((strategy_id, version), []).append(row)

    rankings = {
        engine: tuple(sorted(rows, key=lambda row: (-row.productivity_score, -row.sample_size, row.symbol)))
        for engine, rows in sorted(by_engine.items())
    }
    best_by_symbol: dict[str, OOSProductivityScore] = {}
    for rows in rankings.values():
        for row in rows:
            current = best_by_symbol.get(row.symbol)
            if current is None or (row.productivity_score, row.sample_size, row.strategy_id) > (current.productivity_score, current.sample_size, current.strategy_id):
                best_by_symbol[row.symbol] = row

    payload = {
        "policy": policy.version,
        "fold": policy.oos_fold,
        "rankings": [
            {
                "engine": list(engine),
                "rows": [(row.symbol, row.sample_size, round(row.productivity_score, 12), row.mismatch.preferred_regime, row.mismatch.eligible) for row in rows],
            }
            for engine, rows in sorted(rankings.items())
        ],
    }
    fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return OOSIntelligenceReport(policy.version, policy.oos_fold, rankings, dict(sorted(best_by_symbol.items())), fingerprint)
