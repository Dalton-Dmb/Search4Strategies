from datetime import datetime, timezone

from alphaiq.historical_data import HistoricalBar
from alphaiq.trade_path import PathOutcome, ResearchSide, TradePathRequest, reconstruct_trade_path

UTC = timezone.utc


def bar(ts, high, low, close=100):
    return HistoricalBar(ts, "XAUUSD", "M15", 100, high, low, close, source="fixture")


def test_long_target_and_excursions_are_recorded_in_r():
    request = TradePathRequest("XAUUSD", ResearchSide.LONG, datetime(2026, 1, 1, 10, tzinfo=UTC), 100, 95, 110)
    result = reconstruct_trade_path(request, (
        bar(datetime(2026, 1, 1, 10, tzinfo=UTC), 106, 98),
        bar(datetime(2026, 1, 1, 10, 15, tzinfo=UTC), 111, 99),
    ))
    assert result.outcome is PathOutcome.TARGET
    assert result.outcome_r == 2.0
    assert result.mfe_r >= 2.0
    assert result.mae_r == 0.4


def test_same_bar_stop_and_target_is_ambiguous_not_optimistically_resolved():
    request = TradePathRequest("XAUUSD", ResearchSide.LONG, datetime(2026, 1, 1, 10, tzinfo=UTC), 100, 95, 110)
    result = reconstruct_trade_path(request, (
        bar(datetime(2026, 1, 1, 10, tzinfo=UTC), 111, 94),
    ))
    assert result.outcome is PathOutcome.AMBIGUOUS
    assert result.outcome_r is None


def test_short_stop_is_minus_one_r():
    request = TradePathRequest("XAUUSD", ResearchSide.SHORT, datetime(2026, 1, 1, 10, tzinfo=UTC), 100, 105, 90)
    result = reconstruct_trade_path(request, (
        bar(datetime(2026, 1, 1, 10, tzinfo=UTC), 106, 96),
    ))
    assert result.outcome is PathOutcome.STOP
    assert result.outcome_r == -1.0
