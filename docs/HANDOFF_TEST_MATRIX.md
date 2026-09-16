# AlphaIQ™ Successor Test Matrix

| Domain | Minimum evidence |
|---|---|
| Data | chronology, duplicate, malformed OHLC, gap, timezone, alias and future-data tests |
| Multi-timeframe | higher-TF bar unavailable before close; deterministic snapshot replay |
| Features | insufficient history abstains; provenance/fingerprint stable |
| Regimes | each operational state, ambiguity/UNKNOWN, transition/hysteresis boundaries |
| Strategies | golden, boundary, abstention, no-lookahead, deterministic replay, source lineage |
| Empirical map | dimension isolation, sample gating, fold isolation, metric reproducibility |
| Robustness | bootstrap determinism, annualisation semantics, tail/drawdown/excursion diagnostics |
| KPM-14 | OOS-only, certification exclusion, mismatch sample gate, fingerprint stability |
| ML | temporal leakage/purge, calibration, promotion/rejection, drift/rollback |
| Risk | every veto independently blocks; missing policy fails safe |
| Execution | idempotency, rejects/partials, reconciliation, slippage/latency, restart recovery |
| Deployment | config validation, secrets absent, health/readiness, persistence, restart, rollback |
| Audit | reviewer independence and blocking-finding behavior |

Add regression tests before fixing defects where practical. Never weaken a fail-safe assertion merely to make CI green.
