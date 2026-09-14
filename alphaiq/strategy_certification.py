"""Certification gates for AlphaIQ™ research strategy adapters.

The purpose is to prevent MANIFEST_ONLY or insufficiently verified strategy
logic from being treated as executable research evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .strategy_research import ImplementationState, StrategyResearchSpec


class CertificationStatus(str, Enum):
    CERTIFIED = "CERTIFIED"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class StrategyCertificationEvidence:
    source_ref: str
    golden_test_refs: tuple[str, ...]
    boundary_test_refs: tuple[str, ...]
    no_lookahead_verified: bool
    deterministic_replay_verified: bool
    owner_approved: bool

    def __post_init__(self) -> None:
        if not self.source_ref:
            raise ValueError("source_ref is required")


@dataclass(frozen=True, slots=True)
class StrategyCertificationResult:
    strategy_id: str
    strategy_version: str
    implementation_state: ImplementationState
    status: CertificationStatus
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CatalogueCertificationReport:
    results: tuple[StrategyCertificationResult, ...]

    @property
    def certified_count(self) -> int:
        return sum(item.status is CertificationStatus.CERTIFIED for item in self.results)

    @property
    def blocked_count(self) -> int:
        return sum(item.status is CertificationStatus.BLOCKED for item in self.results)

    def remaining_manifest_only(self) -> tuple[str, ...]:
        return tuple(
            item.strategy_id
            for item in self.results
            if item.implementation_state is ImplementationState.MANIFEST_ONLY
        )


def certify_strategy(
    spec: StrategyResearchSpec,
    evidence: StrategyCertificationEvidence | None,
) -> StrategyCertificationResult:
    if spec.implementation_state is ImplementationState.DISABLED:
        return StrategyCertificationResult(
            spec.strategy_id,
            spec.version,
            spec.implementation_state,
            CertificationStatus.NOT_APPLICABLE,
            ("strategy disabled",),
        )

    blockers: list[str] = []
    if spec.implementation_state is not ImplementationState.IMPLEMENTED:
        blockers.append("approved executable logic not present")
    if evidence is None:
        blockers.append("certification evidence missing")
    else:
        if not evidence.golden_test_refs:
            blockers.append("golden-case tests missing")
        if not evidence.boundary_test_refs:
            blockers.append("boundary tests missing")
        if not evidence.no_lookahead_verified:
            blockers.append("no-lookahead verification missing")
        if not evidence.deterministic_replay_verified:
            blockers.append("deterministic replay verification missing")
        if not evidence.owner_approved:
            blockers.append("owner approval missing")

    return StrategyCertificationResult(
        strategy_id=spec.strategy_id,
        strategy_version=spec.version,
        implementation_state=spec.implementation_state,
        status=CertificationStatus.BLOCKED if blockers else CertificationStatus.CERTIFIED,
        blockers=tuple(blockers),
    )


def certify_catalogue(
    specs: Sequence[StrategyResearchSpec],
    evidence_by_strategy: Mapping[tuple[str, str], StrategyCertificationEvidence],
) -> CatalogueCertificationReport:
    results = [
        certify_strategy(spec, evidence_by_strategy.get((spec.strategy_id, spec.version)))
        for spec in specs
    ]
    return CatalogueCertificationReport(tuple(sorted(results, key=lambda item: (item.strategy_id, item.strategy_version))))
