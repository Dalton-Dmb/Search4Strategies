from datetime import datetime, timedelta, timezone

from alphaiq.domain import JournalEvent
from alphaiq.observability import LearningAnalytics, OutcomeObservation, TraceIndex


BASE = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def event(kind: str, seconds: int, correlation_id: str = "trace-1") -> JournalEvent:
    return JournalEvent(
        event_type=kind,
        payload={"kind": kind},
        timestamp=BASE + timedelta(seconds=seconds),
        correlation_id=correlation_id,
    )


def test_trace_reconstruction_orders_events_and_is_deterministic():
    index = TraceIndex()
    index.extend([event("c", 2), event("a", 0), event("b", 1)])
    trace = index.trace("trace-1")
    assert trace.event_types() == ("a", "b", "c")
    first = trace.fingerprint()

    index2 = TraceIndex()
    index2.extend(reversed([event("c", 2), event("a", 0), event("b", 1)]))
    trace2 = index2.trace("trace-1")
    assert trace2.event_types() == ("a", "b", "c")
    assert len(first) == 64


def test_trace_summaries_group_by_correlation_id():
    index = TraceIndex()
    index.extend([event("a", 0, "x"), event("b", 1, "x"), event("c", 2, "y")])
    summaries = index.summaries()
    assert [item.correlation_id for item in summaries] == ["x", "y"]
    assert [item.event_count for item in summaries] == [2, 1]


def test_learning_analytics_attributes_outcomes():
    outcomes = [
        OutcomeObservation("1", "s1", "ranging", pnl_r=1.0, mae_r=-0.2, mfe_r=1.4, slippage_bps=0.5),
        OutcomeObservation("2", "s1", "ranging", pnl_r=-0.5, mae_r=-0.8, mfe_r=0.3, slippage_bps=1.5),
        OutcomeObservation("3", "s2", "trending", pnl_r=2.0, mae_r=-0.1, mfe_r=2.4, slippage_bps=0.2),
    ]
    analytics = LearningAnalytics()
    by_strategy = analytics.summarize_by_strategy(outcomes)
    assert by_strategy[0].key == "s1"
    assert by_strategy[0].sample_size == 2
    assert by_strategy[0].mean_pnl_r == 0.25

    by_regime = analytics.summarize_by_regime(outcomes)
    assert [item.key for item in by_regime] == ["ranging", "trending"]
