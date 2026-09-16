# AlphaIQ™ Successor Completion Checklist

Use with `docs/DEVELOPER_HANDOFF_FINALITY.md`.

## Baseline
- [ ] Start from current `main` after PR #47; do not resume stale feature branches blindly.
- [ ] Run full CI/tests before modifications and record baseline commit.
- [ ] Inventory open KPM/ALPHA issues and map each to existing modules before adding code.

## Strategy certification
- [ ] Obtain exact approved source for each MANIFEST_ONLY engine.
- [ ] Adapter declares source/version, features and timeframe graph.
- [ ] Golden-case tests pass.
- [ ] Boundary/invalid-state tests pass.
- [ ] No-lookahead/non-repainting tests pass.
- [ ] Deterministic replay passes.
- [ ] Owner approval recorded before IMPLEMENTED/certified status.

## Historical evidence
- [ ] Connect approved historical provider/files through provider-neutral boundary.
- [ ] Canonicalise symbols and UTC/timezone semantics.
- [ ] Validate OHLC, chronology, duplicates, gaps and coverage.
- [ ] Preserve D1/H4/H1/M30/M15/M5 point-in-time close semantics.
- [ ] Generate deterministic dataset/evidence manifests.
- [ ] Assign non-overlapping train/validation/OOS folds.
- [ ] Run regimes, certified strategies, outcomes, excursions and execution assumptions.
- [ ] Generate KPM-12 robustness diagnostics and KPM-14 OOS intelligence.

## ML
- [ ] Train only after clean labelled point-in-time evidence exists.
- [ ] Purged walk-forward validation.
- [ ] Calibration/confusion/abstention diagnostics.
- [ ] Champion/challenger and reproducibility records.
- [ ] Drift baseline and rollback path.

## Remaining engines/features
- [ ] KPM-16 approved chart-pattern definitions integrated and tested.
- [ ] KPM-17 approved DRT/Box Theory definitions integrated and tested.
- [ ] 96-M15 full-day expectation preserved where applicable; missing bars diagnosed.

## Risk/execution
- [ ] Independent risk veto implemented/reconciled.
- [ ] Exposure/drawdown/loss/execution-quality/emergency controls configurable and tested.
- [ ] Idempotent order/state contracts and restart reconciliation tested in non-live modes.
- [ ] Partial/rejected fill, latency and slippage telemetry tested.
- [ ] LIVE remains fail-closed without explicit release approval.

## Contabo package
- [ ] Dockerfile/image.
- [ ] Compose/service orchestration.
- [ ] External secrets; no credentials in repository.
- [ ] Persistent data/model/journal volumes.
- [ ] Health/readiness checks.
- [ ] Structured logs.
- [ ] Restart/recovery tests.
- [ ] Backup/restore, upgrade and rollback runbook.
- [ ] CI packaging/config checks.

## Validation/release
- [ ] Paper/shadow evidence report completed.
- [ ] KPM-07 independent audit completed.
- [ ] No open blocking HIGH/CRITICAL findings.
- [ ] Final release manifest fingerprints code/config/data/features/strategies/regime/models.
- [ ] Owner explicitly approves intended deployment mode.
- [ ] Fresh Contabo VPS deployment reproduced from documentation.
