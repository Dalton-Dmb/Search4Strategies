from datetime import datetime, timezone

import pytest

from alphaiq.evidence_activation import (
    HistoricalRequest,
    ProviderBar,
    build_point_in_time_snapshot,
    build_research_requests,
    ingest_request,
)
from alphaiq.historical_data import HistoricalBar
from alphaiq.instrument_intelligence import default_research_universe

UTC = timezone.utc


class FixtureProvider:
    provider_id = "fixture-feed"
    broker_id = "pepperstone"

    def fetch_bars(self, request):
        return (
            ProviderBar(datetime(2026, 1, 2, 10, 0, tzinfo=UTC), "XAUUSD", 2000, 2005, 1998, 2003, 10),
        )


def test_provider_output_is_normalized_to_canonical_bar():
    universe = default_research_universe()
    request = HistoricalRequest("XAUUSD", "M15", datetime(2026, 1, 2, 9, tzinfo=UTC), datetime(2026, 1, 2, 12, tzinfo=UTC))
    bars = ingest_request(FixtureProvider(), request, universe)
    assert len(bars) == 1
    assert bars[0].symbol == "XAUUSD"
    assert bars[0].source == "fixture-feed"
    assert bars[0].source_symbol == "XAUUSD"


def test_higher_timeframe_bar_is_hidden_until_closed():
    bars = (
        HistoricalBar(datetime(2026, 1, 2, 10, 0, tzinfo=UTC), "XAUUSD", "H1", 2000, 2010, 1995, 2005, source="fixture"),
        HistoricalBar(datetime(2026, 1, 2, 10, 0, tzinfo=UTC), "XAUUSD", "M15", 2000, 2004, 1999, 2002, source="fixture"),
    )
    early = build_point_in_time_snapshot(bars, "XAUUSD", datetime(2026, 1, 2, 10, 15, tzinfo=UTC))
    assert early.latest("M15") is not None
    assert early.latest("H1") is None
    later = build_point_in_time_snapshot(bars, "XAUUSD", datetime(2026, 1, 2, 11, 0, tzinfo=UTC))
    assert later.latest("H1") is not None


def test_research_requests_follow_gold_priority_universe():
    requests = build_research_requests(
        default_research_universe(),
        ("H1", "M15"),
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert requests[0].canonical_symbol == "XAUUSD"
    assert requests[0].timeframe == "H1"
    assert requests[1].canonical_symbol == "XAUUSD"
    assert requests[1].timeframe == "M15"
    assert any(request.canonical_symbol == "USDJPY" for request in requests)


def test_provider_cannot_leak_out_of_range_data():
    class BadProvider(FixtureProvider):
        def fetch_bars(self, request):
            return (ProviderBar(datetime(2027, 1, 1, tzinfo=UTC), "XAUUSD", 1, 1, 1, 1),)

    request = HistoricalRequest("XAUUSD", "M15", datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="outside requested interval"):
        ingest_request(BadProvider(), request, default_research_universe())
