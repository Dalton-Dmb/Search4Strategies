from alphaiq.strategy_certification import (
    CertificationStatus,
    StrategyCertificationEvidence,
    certify_catalogue,
    certify_strategy,
)
from alphaiq.strategy_research import ImplementationState, StrategyResearchSpec, default_strategy_manifest


def implemented_spec():
    return StrategyResearchSpec(
        "example",
        "1.0.0",
        "test",
        frozenset({"RANGE"}),
        frozenset(),
        ImplementationState.IMPLEMENTED,
    )


def complete_evidence(owner_approved=True):
    return StrategyCertificationEvidence(
        source_ref="alphaiq/strategies/example.py@abc123",
        golden_test_refs=("test_example_golden",),
        boundary_test_refs=("test_example_boundary",),
        no_lookahead_verified=True,
        deterministic_replay_verified=True,
        owner_approved=owner_approved,
    )


def test_manifest_only_is_blocked_even_with_evidence():
    spec = default_strategy_manifest()[0]
    result = certify_strategy(spec, complete_evidence())
    assert result.status is CertificationStatus.BLOCKED
    assert "approved executable logic not present" in result.blockers


def test_implemented_strategy_requires_full_verification_and_owner_approval():
    result = certify_strategy(implemented_spec(), complete_evidence(owner_approved=False))
    assert result.status is CertificationStatus.BLOCKED
    assert "owner approval missing" in result.blockers


def test_fully_verified_implemented_strategy_can_be_certified():
    result = certify_strategy(implemented_spec(), complete_evidence())
    assert result.status is CertificationStatus.CERTIFIED
    assert result.blockers == ()


def test_catalogue_report_exposes_remaining_manifest_only_engines():
    manifest = default_strategy_manifest()
    report = certify_catalogue(manifest, {})
    assert report.certified_count == 0
    assert report.blocked_count == len(manifest)
    assert "range_mean_reversion" in report.remaining_manifest_only()
    assert "trinity_steps" in report.remaining_manifest_only()
