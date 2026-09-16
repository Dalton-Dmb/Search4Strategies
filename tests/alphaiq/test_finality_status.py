from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_handoff_status_is_fail_closed_and_does_not_claim_missing_evidence():
    status = yaml.safe_load((ROOT / "docs" / "PROJECT_FINALITY_STATUS.yaml").read_text(encoding="utf-8"))
    assert status["status"]["pr47_kpm14_scope"] == "complete"
    assert status["status"]["external_historical_empirical_run"] == "pending"
    assert status["status"]["full_strategy_certification"] == "pending"
    assert status["status"]["live_authorisation"] == "blocked"
    assert status["invariants"]["no_lookahead"] is True
    assert status["invariants"]["uncertified_strategy_evidence"] == "blocked"
    assert status["invariants"]["live_fail_closed"] is True
