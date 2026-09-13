from datetime import datetime, timezone

import pytest

from alphaiq.shadow_validation import ShadowDecision, ShadowLedger, shadow_summary


def decision(decision_id: str = "d1", side: str = "FLAT") -> ShadowDecision:
    return ShadowDecision(
        decision_id=decision_id,
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc),
        symbol="XAUUSD",
        timeframe="M15",
        regime="RANGE",
        regime_confidence=0.82,
        strategy_id=None if side == "FLAT" else "range_mean_reversion",
        strategy_version=None if side == "FLAT" else "1.0.0",
        research_side=side,
        feature_fingerprint="features-v1",
        configuration_version="config-v1",
        model_version=None,
        reason="shadow-only research decision",
    )


def test_shadow_ledger_rejects_duplicate_decisions():
    ledger = ShadowLedger()
    ledger.record(decision())
    with pytest.raises(ValueError, match="duplicate decision_id"):
        ledger.record(decision())


def test_outcome_attachment_is_one_time_and_replayable():
    ledger = ShadowLedger()
    ledger.record(decision("d1", "LONG"))
    before = ledger.fingerprint()
    ledger.attach_outcome("d1", 1.5)
    after = ledger.fingerprint()
    assert before != after
    assert ledger.decisions()[0].outcome_r == 1.5
    with pytest.raises(ValueError, match="already attached"):
        ledger.attach_outcome("d1", 0.5)


def test_summary_tracks_abstention_and_outcomes():
    ledger = ShadowLedger()
    ledger.record(decision("d1", "FLAT"))
    ledger.record(decision("d2", "LONG"))
    ledger.attach_outcome("d2", 2.0)
    summary = shadow_summary(ledger.decisions())
    assert summary["decisions"] == 2
    assert summary["flat_decisions"] == 1
    assert summary["abstention_rate"] == pytest.approx(0.5)
    assert summary["mean_outcome_r"] == pytest.approx(2.0)


def test_naive_timestamp_and_invalid_side_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        ShadowDecision(
            "x", datetime(2026, 1, 1), "XAUUSD", "M15", "RANGE", 0.8,
            None, None, "FLAT", "f", "c"
        )
    with pytest.raises(ValueError, match="LONG, SHORT or FLAT"):
        ShadowDecision(
            "x", datetime(2026, 1, 1, tzinfo=timezone.utc), "XAUUSD", "M15", "RANGE", 0.8,
            None, None, "BUY", "f", "c"
        )
