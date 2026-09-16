from pathlib import Path


DOCS = Path(__file__).resolve().parents[2] / "docs"


def test_finality_handoff_contains_critical_fail_closed_invariants():
    text = (DOCS / "DEVELOPER_HANDOFF_FINALITY.md").read_text(encoding="utf-8")
    required = (
        "No look-ahead",
        "MANIFEST_ONLY",
        "LIVE must fail closed",
        "Do not invent proprietary strategy formulas",
        "Genuine empirical evidence activation",
        "Contabo production packaging",
        "Definition of finality",
    )
    for phrase in required:
        assert phrase in text


def test_successor_prompt_points_to_authoritative_handoff_and_preserves_oos_gate():
    text = (DOCS / "SUCCESSOR_PROMPT.md").read_text(encoding="utf-8")
    assert "DEVELOPER_HANDOFF_FINALITY.md" in text
    assert "train/validation/OOS isolation" in text
    assert "keep LIVE fail-closed" in text
    assert "never invent missing proprietary trading formulas" in text


def test_pr47_completion_note_does_not_claim_external_validation():
    text = (DOCS / "PR47_COMPLETION_NOTE.md").read_text(encoding="utf-8")
    assert "merged and complete for its stated scope" in text
    assert "does **not** assert that genuine external historical observations" in text
