"""Operational, research-only regime labelling for AlphaIQ™.

All decision thresholds are supplied explicitly through configuration. The
module contains no hidden production thresholds and returns UNKNOWN when
required evidence is missing or materially ambiguous.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class OperationalRegime(str, Enum):
    UNKNOWN = "UNKNOWN"
    STRONG_TREND = "STRONG_TREND"
    WEAK_TREND = "WEAK_TREND"
    RANGE = "RANGE"
    COMPRESSION = "COMPRESSION"
    EXPANSION = "EXPANSION"
    TRANSITION = "TRANSITION"
    EVENT_SHOCK = "EVENT_SHOCK"
    CHOP = "CHOP"


@dataclass(frozen=True, slots=True)
class RegimeEvidence:
    trend_strength: float | None = None
    directional_efficiency: float | None = None
    volatility_percentile: float | None = None
    compression_score: float | None = None
    expansion_score: float | None = None
    mean_reversion_score: float | None = None
    transition_score: float | None = None
    event_abnormality: float | None = None
    liquidity_quality: float | None = None

    def values(self) -> Mapping[str, float | None]:
        return {
            "trend_strength": self.trend_strength,
            "directional_efficiency": self.directional_efficiency,
            "volatility_percentile": self.volatility_percentile,
            "compression_score": self.compression_score,
            "expansion_score": self.expansion_score,
            "mean_reversion_score": self.mean_reversion_score,
            "transition_score": self.transition_score,
            "event_abnormality": self.event_abnormality,
            "liquidity_quality": self.liquidity_quality,
        }


@dataclass(frozen=True, slots=True)
class RegimeThresholds:
    version: str
    strong_trend_min: float
    weak_trend_min: float
    efficiency_min: float
    range_mean_reversion_min: float
    compression_min: float
    expansion_min: float
    transition_min: float
    event_shock_min: float
    chop_liquidity_max: float
    ambiguity_margin: float
    minimum_evidence_count: int = 3

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("threshold configuration version is required")
        numeric = (
            self.strong_trend_min, self.weak_trend_min, self.efficiency_min,
            self.range_mean_reversion_min, self.compression_min, self.expansion_min,
            self.transition_min, self.event_shock_min, self.chop_liquidity_max,
            self.ambiguity_margin,
        )
        if any(not 0.0 <= x <= 1.0 for x in numeric):
            raise ValueError("all thresholds must be normalized to [0, 1]")
        if self.strong_trend_min < self.weak_trend_min:
            raise ValueError("strong trend threshold must be >= weak trend threshold")
        if self.minimum_evidence_count < 1:
            raise ValueError("minimum_evidence_count must be positive")


@dataclass(frozen=True, slots=True)
class RegimeLabelResult:
    regime: OperationalRegime
    confidence: float
    threshold_version: str
    reason: str
    candidate_scores: Mapping[OperationalRegime, float]


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def label_regime(evidence: RegimeEvidence, config: RegimeThresholds) -> RegimeLabelResult:
    supplied = {k: v for k, v in evidence.values().items() if v is not None}
    if len(supplied) < config.minimum_evidence_count:
        return RegimeLabelResult(
            OperationalRegime.UNKNOWN, 0.0, config.version,
            "insufficient evidence", {},
        )

    scores: dict[OperationalRegime, float] = {}

    if evidence.event_abnormality is not None and evidence.event_abnormality >= config.event_shock_min:
        scores[OperationalRegime.EVENT_SHOCK] = _clamp01(evidence.event_abnormality)

    if evidence.transition_score is not None and evidence.transition_score >= config.transition_min:
        scores[OperationalRegime.TRANSITION] = _clamp01(evidence.transition_score)

    if evidence.expansion_score is not None and evidence.expansion_score >= config.expansion_min:
        scores[OperationalRegime.EXPANSION] = _clamp01(evidence.expansion_score)

    if evidence.compression_score is not None and evidence.compression_score >= config.compression_min:
        scores[OperationalRegime.COMPRESSION] = _clamp01(evidence.compression_score)

    trend = evidence.trend_strength
    eff = evidence.directional_efficiency
    if trend is not None and eff is not None and eff >= config.efficiency_min:
        if trend >= config.strong_trend_min:
            scores[OperationalRegime.STRONG_TREND] = _clamp01((trend + eff) / 2)
        elif trend >= config.weak_trend_min:
            scores[OperationalRegime.WEAK_TREND] = _clamp01((trend + eff) / 2)

    if evidence.mean_reversion_score is not None and evidence.mean_reversion_score >= config.range_mean_reversion_min:
        trend_penalty = trend if trend is not None else 0.0
        range_score = evidence.mean_reversion_score * (1.0 - 0.5 * trend_penalty)
        scores[OperationalRegime.RANGE] = _clamp01(range_score)

    if evidence.liquidity_quality is not None and evidence.liquidity_quality <= config.chop_liquidity_max:
        inverse_quality = 1.0 - evidence.liquidity_quality
        low_eff = 1.0 - (eff if eff is not None else 0.5)
        scores[OperationalRegime.CHOP] = _clamp01((inverse_quality + low_eff) / 2)

    if not scores:
        return RegimeLabelResult(
            OperationalRegime.UNKNOWN, 0.0, config.version,
            "no configured regime threshold satisfied", {},
        )

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0].value))
    winner, top = ranked[0]
    if len(ranked) > 1:
        margin = top - ranked[1][1]
        if margin < config.ambiguity_margin:
            return RegimeLabelResult(
                OperationalRegime.UNKNOWN, top, config.version,
                f"ambiguous candidates; margin={margin:.6f}", dict(ranked),
            )

    return RegimeLabelResult(winner, top, config.version, "configured evidence winner", dict(ranked))
