from alphaiq.audit_readiness import (
    AuditEvidence,
    AuditFinding,
    FindingSeverity,
    FindingStatus,
    assess_research_release_readiness,
    severity_counts,
)


def base_evidence(**overrides):
    values = dict(
        reviewer="independent-reviewer",
        reviewer_is_independent=True,
        ci_green=True,
        oos_validation_completed=True,
        point_in_time_review_completed=True,
        reproducibility_review_completed=True,
        journal_trace_review_completed=True,
        findings=(),
    )
    values.update(overrides)
    return AuditEvidence(**values)


def test_ready_requires_independent_reviewer_and_all_core_gates():
    decision = assess_research_release_readiness(base_evidence())
    assert decision.ready_for_research_release is True


def test_same_agent_cannot_self_certify():
    decision = assess_research_release_readiness(base_evidence(reviewer_is_independent=False))
    assert decision.ready_for_research_release is False
    assert "independent reviewer required" in decision.reason


def test_open_high_or_critical_findings_block_readiness():
    finding = AuditFinding(
        "F-1", "leakage", FindingSeverity.CRITICAL, FindingStatus.OPEN, "future timestamp used"
    )
    decision = assess_research_release_readiness(base_evidence(findings=(finding,)))
    assert decision.ready_for_research_release is False
    assert decision.unresolved_high_or_critical == ("F-1",)


def test_remediated_high_finding_no_longer_blocks_if_other_gates_pass():
    finding = AuditFinding(
        "F-2", "reproducibility", FindingSeverity.HIGH, FindingStatus.REMEDIATED, "seed mismatch"
    )
    decision = assess_research_release_readiness(base_evidence(findings=(finding,)))
    assert decision.ready_for_research_release is True


def test_severity_counts_are_complete_and_deterministic():
    findings = [
        AuditFinding("L", "docs", FindingSeverity.LOW, FindingStatus.OPEN, "minor"),
        AuditFinding("H", "leakage", FindingSeverity.HIGH, FindingStatus.OPEN, "major"),
    ]
    counts = severity_counts(findings)
    assert counts[FindingSeverity.LOW] == 1
    assert counts[FindingSeverity.HIGH] == 1
    assert counts[FindingSeverity.MEDIUM] == 0
    assert counts[FindingSeverity.CRITICAL] == 0
