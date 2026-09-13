"""Standardized research-only strategy integration for AlphaIQ™.

The contracts in this module normalize strategy identity, feature requirements,
regime compatibility and research signals. They do not submit orders. Strategy
logic that is not yet present in the repository is represented explicitly as
MANIFEST_ONLY rather than guessed or silently invented.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Protocol, Sequence


class ResearchSignalSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class ImplementationState(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    MANIFEST_ONLY = "MANIFEST_ONLY"
    DISABLED = "DISABLED"


@dataclass(frozen=True, slots=True)
class StrategyResearchSpec:
    strategy_id: str
    version: str
    family: str
    compatible_regimes: frozenset[str]
    required_features: frozenset[str]
    implementation_state: ImplementationState = ImplementationState.MANIFEST_ONLY
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.strategy_id or not self.version or not self.family:
            raise ValueError("strategy identity, version and family are required")
        if not self.compatible_regimes:
            raise ValueError("at least one compatible regime is required")


@dataclass(frozen=True, slots=True)
class StrategyResearchContext:
    regime: str
    features: Mapping[str, float]
    as_of_iso: str


@dataclass(frozen=True, slots=True)
class StrategyResearchSignal:
    strategy_id: str
    strategy_version: str
    side: ResearchSignalSide
    confidence: float
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be normalized to [0, 1]")


class ResearchStrategyAdapter(Protocol):
    spec: StrategyResearchSpec

    def evaluate(self, context: StrategyResearchContext) -> StrategyResearchSignal: ...


class ManifestOnlyAdapter:
    """Fail-safe adapter used until approved executable research logic exists."""

    def __init__(self, spec: StrategyResearchSpec) -> None:
        self.spec = spec

    def evaluate(self, context: StrategyResearchContext) -> StrategyResearchSignal:
        if self.spec.implementation_state is not ImplementationState.MANIFEST_ONLY:
            raise ValueError("ManifestOnlyAdapter requires MANIFEST_ONLY specification")
        return StrategyResearchSignal(
            self.spec.strategy_id,
            self.spec.version,
            ResearchSignalSide.FLAT,
            0.0,
            "approved research logic not present; abstaining",
        )


class StrategyResearchRegistry:
    def __init__(self, specs: Sequence[StrategyResearchSpec] = ()) -> None:
        self._specs: dict[tuple[str, str], StrategyResearchSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: StrategyResearchSpec) -> None:
        key = (spec.strategy_id, spec.version)
        if key in self._specs:
            raise ValueError(f"duplicate strategy specification: {key}")
        self._specs[key] = spec

    def get(self, strategy_id: str, version: str) -> StrategyResearchSpec:
        try:
            return self._specs[(strategy_id, version)]
        except KeyError as exc:
            raise KeyError(f"unregistered strategy: {(strategy_id, version)}") from exc

    def eligible_specs(self, regime: str, available_features: set[str]) -> tuple[StrategyResearchSpec, ...]:
        eligible = []
        for spec in self._specs.values():
            if spec.implementation_state is ImplementationState.DISABLED:
                continue
            if regime not in spec.compatible_regimes:
                continue
            if not spec.required_features.issubset(available_features):
                continue
            eligible.append(spec)
        return tuple(sorted(eligible, key=lambda s: (s.strategy_id, s.version)))


def default_strategy_manifest() -> tuple[StrategyResearchSpec, ...]:
    """Project strategy catalogue without invented execution formulas.

    Compatibility is broad research categorization from the AlphaIQ™ manual;
    final empirical routing remains governed by the performance matrix.
    """
    M = ImplementationState.MANIFEST_ONLY
    return (
        StrategyResearchSpec("trend_continuation", "1.0.0", "trend", frozenset({"STRONG_TREND", "WEAK_TREND"}), frozenset({"trend_strength", "directional_efficiency"}), M),
        StrategyResearchSpec("breakout_expansion", "1.0.0", "breakout", frozenset({"COMPRESSION", "EXPANSION"}), frozenset({"compression_score", "expansion_score"}), M),
        StrategyResearchSpec("range_mean_reversion", "1.0.0", "mean_reversion", frozenset({"RANGE"}), frozenset({"mean_reversion_score"}), M),
        StrategyResearchSpec("reversal_transition", "1.0.0", "reversal", frozenset({"TRANSITION"}), frozenset({"transition_score"}), M),
        StrategyResearchSpec("spoton", "1.0.0", "session_open", frozenset({"EXPANSION", "TRANSITION", "EVENT_SHOCK"}), frozenset({"daily_atr_ratio", "session_phase"}), M),
        StrategyResearchSpec("rrrb_rrrs", "1.0.0", "standalone_signal", frozenset({"STRONG_TREND", "WEAK_TREND", "RANGE", "TRANSITION"}), frozenset(), M),
        StrategyResearchSpec("utbmachine", "1.0.0", "trend_structure", frozenset({"STRONG_TREND", "WEAK_TREND"}), frozenset({"trend_strength"}), M),
        StrategyResearchSpec("trinity_steps", "1.0.0", "liquidity_structure", frozenset({"TRANSITION", "EXPANSION", "WEAK_TREND"}), frozenset({"liquidity_sweep", "structure_break", "fvg_present"}), M),
        StrategyResearchSpec("golden_goose_smt", "1.0.0", "intermarket", frozenset({"TRANSITION", "RANGE", "WEAK_TREND"}), frozenset({"smt_divergence"}), M),
        StrategyResearchSpec("unicorn", "1.0.0", "confluence", frozenset({"TRANSITION", "WEAK_TREND", "STRONG_TREND"}), frozenset({"htf_poi", "liquidity_sweep", "structure_break"}), M),
    )
