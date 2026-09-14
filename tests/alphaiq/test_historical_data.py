from datetime import datetime, timedelta, timezone

import pytest

from alphaiq.historical_data import (
    DatasetQualityPolicy,
    EvidenceRunManifest,
    FoldBoundary,
    HistoricalBar,
    assign_fold,
    build_dataset_manifest,
    canonicalize_symbol,
    dataset_fingerprint,
    validate_dataset,
    validate_fold_boundaries,
)
from alphaiq.instrument_intelligence import InstrumentSpec, InstrumentUniverse

UTC = timezone.utc


def bar(i: int, symbol: str = "XAUUSD", timeframe: str = "M15") -> HistoricalBar:
    ts = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=15 * i)
    return HistoricalBar(ts, symbol, timeframe, 100.0, 102.0, 99.0, 101.0, 10.0, "fixture")


def test_bar_rejects_malformed_ohlc_and_naive_timestamp():
    with pytest.raises(ValueError):
        HistoricalBar(datetime(2026, 1, 1), "XAUUSD", "M15", 100, 101, 99, 100, source="fixture")
    with pytest.raises(ValueError):
        HistoricalBar(datetime(2026, 1, 1, tzinfo=UTC), "XAUUSD", "M15", 100, 100, 99, 101, source="fixture")


def test_dataset_fingerprint_is_order_independent_and_content_sensitive():
    a = [bar(0), bar(1)]
    b = [bar(1), bar(0)]
    assert dataset_fingerprint(a) == dataset_fingerprint(b)
    changed = [bar(0), HistoricalBar(bar(1).timestamp, "XAUUSD", "M15", 100, 103, 99, 102, 10, "fixture")]
    assert dataset_fingerprint(a) != dataset_fingerprint(changed)


def test_quality_report_detects_duplicate_nonchronology_and_gap():
    policy = DatasetQualityPolicy("q1", maximum_gap_multiple=2)
    duplicate = [bar(0), bar(0)]
    report = validate_dataset(duplicate, policy)
    assert report.valid is False
    assert report.duplicate_count == 1
    assert report.chronology_errors == 1

    gapped = [bar(0), bar(4)]
    gap_report = validate_dataset(gapped, policy)
    assert gap_report.valid is False
    assert gap_report.excessive_gap_count == 1


def test_manifest_requires_quality_and_is_reproducible():
    bars = [bar(i) for i in range(4)]
    policy = DatasetQualityPolicy("q1")
    created = datetime(2026, 2, 1, tzinfo=UTC)
    manifest = build_dataset_manifest("gold-m15", "v1", bars, policy, created)
    assert manifest.bar_count == 4
    assert manifest.symbols == ("XAUUSD",)
    assert manifest.fingerprint == dataset_fingerprint(bars)

    with pytest.raises(ValueError):
        build_dataset_manifest("bad", "v1", [bar(0), bar(0)], policy, created)


def test_broker_alias_resolves_to_canonical_symbol():
    universe = InstrumentUniverse(
        "u-test",
        (
            InstrumentSpec("XAUUSD", "METAL", 100, broker_aliases={"pepperstone": "GOLD"}),
            InstrumentSpec("USDJPY", "FX", 90, broker_aliases={"deriv": "USDJPY.a"}),
        ),
    )
    assert canonicalize_symbol("gold", universe, "pepperstone") == "XAUUSD"
    assert canonicalize_symbol("USDJPY.a", universe, "deriv") == "USDJPY"
    assert canonicalize_symbol("XAUUSD", universe) == "XAUUSD"
    with pytest.raises(KeyError):
        canonicalize_symbol("UNKNOWN", universe)


def test_fold_assignment_and_overlap_guard():
    folds = (
        FoldBoundary("train", datetime(2024, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC)),
        FoldBoundary("validation", datetime(2025, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, tzinfo=UTC)),
        FoldBoundary("oos", datetime(2026, 1, 1, tzinfo=UTC), datetime(2027, 1, 1, tzinfo=UTC)),
    )
    validate_fold_boundaries(folds)
    assert assign_fold(datetime(2026, 6, 1, tzinfo=UTC), folds) == "oos"
    with pytest.raises(ValueError):
        assign_fold(datetime(2028, 1, 1, tzinfo=UTC), folds)

    overlapping = (
        FoldBoundary("a", datetime(2024, 1, 1, tzinfo=UTC), datetime(2025, 6, 1, tzinfo=UTC)),
        FoldBoundary("b", datetime(2025, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, tzinfo=UTC)),
    )
    with pytest.raises(ValueError):
        validate_fold_boundaries(overlapping)


def test_evidence_run_fingerprint_is_deterministic_and_version_sensitive():
    created = datetime(2026, 9, 14, tzinfo=UTC)
    run = EvidenceRunManifest("run-1", created, "data-a", "features-a", "regime-1", "strategies-1", "empirical-1", "code-1", "u1")
    same = EvidenceRunManifest("run-1", created, "data-a", "features-a", "regime-1", "strategies-1", "empirical-1", "code-1", "u1")
    changed = EvidenceRunManifest("run-1", created, "data-a", "features-a", "regime-1", "strategies-2", "empirical-1", "code-1", "u1")
    assert run.fingerprint() == same.fingerprint()
    assert run.fingerprint() != changed.fingerprint()
