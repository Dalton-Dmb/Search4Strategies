# AlphaIQ™ Point-in-Time Data & Feature Platform

## Purpose

ALPHA-001 establishes the permanent market-data and feature-computation layer used by research, backtest, walk-forward, paper, shadow and live modes. The governing principle is **point-in-time equivalence**: a feature available at time `t` may only depend on information that was available at or before `t`.

## Production invariants

1. Every market observation carries a timezone-aware timestamp, symbol, timeframe and source.
2. Future observations are rejected by default.
3. Stale data causes a fail-safe invalid result rather than silent continuation.
4. Feature definitions are versioned and registered in a catalog.
5. A feature-set fingerprint is deterministic and changes when the approved feature manifest changes.
6. Feature vectors include provenance per feature.
7. Insufficient history causes abstention/failure-safe behavior.
8. Replay exposes only the history available at each replay timestamp.
9. Storage/provider implementations are adapters; domain logic remains provider-neutral.
10. Existing `app/features/*` research functions remain available but are not automatically production-approved. They must be wrapped/validated through the point-in-time platform before use by AlphaIQ™.

## Components

- `alphaiq.data_platform`: symbol/timeframe normalization, quality/freshness policy, point-in-time validation and storage protocol.
- `alphaiq.feature_platform`: versioned feature specifications, deterministic catalog fingerprinting and point-in-time feature engine.
- `alphaiq.replay`: deterministic chronological replay with no future-data exposure.
- `tests/alphaiq/test_data_feature_platform.py`: leakage, staleness, fingerprint, replay and provenance tests.

## Feature families

The platform is intentionally agnostic to trading thresholds. The AlphaIQ™ Specification Manual will authorize concrete features and formulas across trend, momentum, volatility, range/mean-reversion, market structure, liquidity, session/time, intermarket/SMT, execution-quality and event-context families.

No feature becomes production-approved merely because it exists in the research library. Approval requires a version, point-in-time semantics, provenance, tests and inclusion in the controlled feature catalog.

## Offline/online parity

The same `FeatureSpec` and point-in-time semantics are intended for historical replay and live inference. Provider-specific ingestion may differ, but the normalized observation and feature contracts must not.

## Fail-safe behavior

When data is missing, stale, non-monotonic, from the future, or history is insufficient, the platform returns an invalid build result. Downstream regime, strategy and execution components must treat this as an abstention condition rather than guessing or filling silently.
