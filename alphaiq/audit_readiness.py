"""Independent validation audit/readiness dossier contracts for AlphaIQ™.

This module records review findings and release-readiness evidence. It does not
self-certify the system: a final READY decision requires all critical/high
findings resolved and an explicitly independent reviewer identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class FindingSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingStatus(str, Enum):
    OPEN = "OPEN"
    REMEDIATED = "REMEDIATED"
    ACCEPTED = "ACCEPTED"


@dataclass(frozen=True, slots=True)
class AuditFinding:
    finding_id: str
    category: str
    severity: FindingSeverity
    status: FindingStatus
    summary: str
    evidence: str = ""

    def __post_init__(self) -> None:
        if not self.finding_id or not self.category or not self.summary:
            raise ValueError("finding identity, category and summary are required")


@dataclass(frozen=True, slots=True)
class AuditEvidence:
    reviewer: str
    reviewer_is_independent: bool
    ci_green: bool
    oos_validation_completed: bool
    point_in_time_review_completed: bool
    reproducibility_review_completed: bool
    journal_trace_review_completed: bool
    findings: tuple[AuditFinding, ...] = ()


@dataclass(frozen=True, slots=True)
class ReadinessDecision:
    ready_for_research_release: bool
    reason: str
    unresolved_high_or_critical: tuple[str, ...]


def assess_research_release_readiness(evidence: AuditEvidence) -> ReadinessDecision:
    blockers: list[str] = []
    if not evidence.reviewer.strip():
        blockers.append("reviewer identity missing")
    if not evidence.reviewer_is_independent:
        blockers.append("independent reviewer required")
    if not evidence.ci_green:
        blockers.append("CI is not green")
    if not evidence.oos_validation_completed:
        blockers.append("out-of-sample validation incomplete")
    if not evidence.point_in_time_review_completed:
        blockers.append("point-in-time review incomplete")
    if not evidence.reproducibility_review_completed:
        blockers.append("reproducibility review incomplete")
    if not evidence.journal_trace_review_completed:
        blockers.append("journal trace review incomplete")

    unresolved = tuple(
        f.finding_id
        for f in evidence.findings
        if f.severity in {FindingSeverity.HIGH, FindingSeverity.CRITICAL}
        and f.status is FindingStatus.OPEN
    )
    if unresolved:
        blockers.append("unresolved high/critical findings")

    if blockers:
        return ReadinessDecision(False, "; ".join(blockers), unresolved)
    return ReadinessDecision(True, "independent research-release gates satisfied", ())


def severity_counts(findings: Iterable[AuditFinding]) -> dict[FindingSeverity, int]:
    counts = {severity: 0 for severity in FindingSeverity}
    for finding in findings:
        counts[finding.severity] += 1
    return counts
