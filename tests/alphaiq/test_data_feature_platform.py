from datetime import datetime, timedelta, timezone

from alphaiq.data_platform import DataQualityPolicy, InMemorySnapshotStore, validate_point_in_time
from alphaiq.domain import MarketSnapshot
from alphaiq.feature_platform import (
    FeatureCatalog,
    FeatureSpec,
    PointInTimeFeatureEngine,
    candle_body,
    candle_range,
    close_return_1,
)
from alphaiq.replay import DeterministicReplay


def snap(minute: int, close: float = 100.5) -> MarketSnapshot:
    return MarketSnapshot(
        symbol="xauusd",
        timeframe="m15",
        timestamp=datetime(2026, 1, 1, 10, minute, tzinfo=timezone.utc),
        open=100.0,
        high=max(101.0, close),
        low=min(99.0, close),
        close=close,
        volume=1.0,
        source="test",
    )


def test_future_observation_is_rejected():
    policy = DataQualityPolicy(max_age=timedelta(hours=1))
    report = validate_point_in_time(
        [snap(0), snap(15)],
        as_of=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        policy=policy,
    )
    assert report.valid is False
    assert "future_observation" in report.reasons


def test_stale_data_is_rejected():
    policy = DataQualityPolicy(max_age=timedelta(minutes=10))
    report = validate_point_in_time(
        [snap(0)],
        as_of=datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc),
        policy=policy,
    )
    assert report.valid is False
    assert "stale_data" in report.reasons


def test_store_normalizes_symbol_and_timeframe():
    store = InMemorySnapshotStore()
    store.append(snap(0))
    values = store.read(
        symbol=" XAUUSD ",
        timeframe="M15",
        start=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
    )
    assert len(values) == 1


def test_feature_catalog_fingerprint_is_deterministic():
    a = FeatureCatalog()
    a.register(FeatureSpec("range", "1", "candle", 1, candle_range))
    a.register(FeatureSpec("body", "1", "candle", 1, candle_body))

    b = FeatureCatalog()
    b.register(FeatureSpec("body", "1", "candle", 1, candle_body))
    b.register(FeatureSpec("range", "1", "candle", 1, candle_range))

    assert a.fingerprint() == b.fingerprint()


def test_point_in_time_feature_engine_builds_versioned_vector():
    catalog = FeatureCatalog()
    catalog.register(FeatureSpec("range", "1", "candle", 1, candle_range))
    catalog.register(FeatureSpec("body", "1", "candle", 1, candle_body))
    catalog.register(FeatureSpec("return_1", "1", "return", 2, close_return_1))
    engine = PointInTimeFeatureEngine(catalog, DataQualityPolicy(max_age=timedelta(hours=1)))

    result = engine.build(
        [snap(0, 100.0), snap(15, 101.0)],
        as_of=datetime(2026, 1, 1, 10, 15, tzinfo=timezone.utc),
    )

    assert result.valid is True
    assert result.vector is not None
    assert result.vector.feature_set_version == catalog.fingerprint()
    assert result.vector.values["return_1"] == 0.01
    assert "return_1" in result.vector.provenance


def test_insufficient_history_fails_safe():
    catalog = FeatureCatalog()
    catalog.register(FeatureSpec("return_1", "1", "return", 2, close_return_1))
    engine = PointInTimeFeatureEngine(catalog, DataQualityPolicy(max_age=timedelta(hours=1)))
    result = engine.build([snap(0)], as_of=snap(0).timestamp)
    assert result.valid is False
    assert result.vector is None
    assert result.reasons == ("insufficient_history:return_1",)


def test_replay_is_deterministic_and_never_exposes_future():
    source = [snap(30, 103.0), snap(0, 100.0), snap(15, 101.0)]
    replay_a = DeterministicReplay(source)
    replay_b = DeterministicReplay(list(reversed(source)))
    assert replay_a.signature() == replay_b.signature()

    steps = list(replay_a.steps())
    assert [len(step.history) for step in steps] == [1, 2, 3]
    for step in steps:
        assert all(item.timestamp <= step.as_of for item in step.history)
