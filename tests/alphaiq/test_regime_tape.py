from datetime import datetime, timezone

from alphaiq.historical_data import HistoricalBar
from alphaiq.regime_labelling import OperationalRegime, RegimeEvidence, RegimeThresholds
from alphaiq.regime_tape import build_regime_tape

UTC = timezone.utc


class FixtureExtractor:
    version = "fixture-v1"

    def extract(self, snapshot):
        latest_h1 = snapshot.latest("H1")
        trend = 0.9 if latest_h1 and latest_h1.close > latest_h1.open else 0.2
        return RegimeEvidence(
            trend_strength=trend,
            directional_efficiency=0.9,
            mean_reversion_score=0.1,
        )


def thresholds():
    return RegimeThresholds(
        version="t1",
        strong_trend_min=0.8,
        weak_trend_min=0.5,
        efficiency_min=0.6,
        range_mean_reversion_min=0.8,
        compression_min=0.8,
        expansion_min=0.8,
        transition_min=0.8,
        event_shock_min=0.8,
        chop_liquidity_max=0.2,
        ambiguity_margin=0.05,
        minimum_evidence_count=3,
    )


def test_regime_tape_respects_higher_timeframe_close_boundary():
    bars = (
        HistoricalBar(datetime(2026, 1, 2, 10, 0, tzinfo=UTC), "XAUUSD", "H1", 100, 111, 99, 110, source="fixture"),
        HistoricalBar(datetime(2026, 1, 2, 10, 0, tzinfo=UTC), "XAUUSD", "M15", 100, 102, 99, 101, source="fixture"),
        HistoricalBar(datetime(2026, 1, 2, 10, 15, tzinfo=UTC), "XAUUSD", "M15", 101, 103, 100, 102, source="fixture"),
        HistoricalBar(datetime(2026, 1, 2, 10, 30, tzinfo=UTC), "XAUUSD", "M15", 102, 104, 101, 103, source="fixture"),
        HistoricalBar(datetime(2026, 1, 2, 10, 45, tzinfo=UTC), "XAUUSD", "M15", 103, 111, 102, 110, source="fixture"),
    )
    tape = build_regime_tape(bars, "XAUUSD", "M15", FixtureExtractor(), thresholds())
    assert len(tape.points) == 4
    assert tape.points[0].regime is OperationalRegime.UNKNOWN
    assert tape.points[-1].regime is OperationalRegime.STRONG_TREND
    assert tape.points[-1].evidence_version == "fixture-v1"
