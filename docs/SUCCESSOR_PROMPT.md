# AlphaIQ™ One-Swoop Successor Developer Prompt

You are the successor lead developer for **AlphaIQ™ Market Regime / AlphaIQ™ Market Regime Classification Engine** in `Dalton-Dmb/Search4Strategies`.

Read first:
1. `docs/DEVELOPER_HANDOFF_FINALITY.md`
2. `docs/HANDOFF_CHECKLIST.md`
3. `docs/PR47_COMPLETION_NOTE.md`
4. Existing AlphaIQ™ architecture/data/ML/audit documentation and tests.

Your mandate is to take the current `main` after merged PR #47 to a reproducible release candidate and documented Contabo deployment without redesigning the system.

Non-negotiable constraints: preserve point-in-time/no-lookahead behavior; abstain on unknown/insufficient evidence; never treat MANIFEST_ONLY/uncertified strategies as executable evidence; never invent missing proprietary trading formulas; keep canonical instruments broker-neutral; keep Gold prioritised but not exclusive; preserve H1 thesis with M30/M15 and strategy-specific M5 refinement; maintain train/validation/OOS isolation; maintain deterministic fingerprints and full lineage; keep ML governed rather than unconstrained; keep risk as an independent veto; keep LIVE fail-closed; commit no secrets; do not interpret deployment as permission for real-money execution.

Execution order:

1. Inventory current `main`, open issues and tests; run baseline CI/tests.
2. Locate/import exact approved strategy source logic. Certify each only after source lineage, golden/boundary/no-lookahead/deterministic replay tests and owner approval. Leave unavailable engines MANIFEST_ONLY.
3. Connect approved real historical market/event data through the KPM-13 provider boundary. Validate chronology/OHLC/duplicates/gaps/timezones and generate deterministic manifests across the configured Gold-priority multi-asset universe and D1/H4/H1/M30/M15/M5 hierarchy.
4. Execute the complete point-in-time evidence pipeline: features → regime labels → certified strategy decisions → outcomes/MFE/MAE/execution assumptions → folds → empirical map → KPM-12 diagnostics → KPM-14 OOS productivity and regime-mismatch report. Archive fingerprints and reports.
5. Only after clean labelled evidence exists, train/evaluate the KPM-05 regime/meta-model using purged walk-forward validation, calibration, champion/challenger governance, drift baselines and reproducible manifests. No unapproved champion.
6. Implement KPM-16 chart-pattern research adapters only from approved definitions; machine geometry/evidence is separate from Pine visual aids. Implement KPM-17 DRT/Box Theory only from approved definitions; preserve session/day vs weekly/monthly distinction and 96-M15 expectation where applicable.
7. Reconcile ALPHA-005 risk and ALPHA-007 execution requirements against current architecture from fresh branches. Implement deterministic risk vetoes, non-live execution lifecycle/reconciliation, fill/slippage/latency telemetry and restart recovery. Do not bypass live gates.
8. Complete KPM-15: Docker image, compose/service orchestration, external secrets, persistent volumes, health/readiness, structured logs, restart recovery, backup/restore, upgrade/rollback, CI packaging checks and Contabo runbook.
9. Run paper/shadow validation and produce evidence report. Complete KPM-07 with an independent reviewer. Resolve all blocking HIGH/CRITICAL findings.
10. Produce a deterministic final release manifest tying code commit, configuration, datasets, features, regimes, strategies, models, broker routes, evidence reports and approvals together. Reproduce installation on a fresh Contabo VPS.

Use small reviewable PRs and green CI throughout, but treat the objective as one coherent release. Do not stop merely because an ordinary engineering problem occurs: diagnose, test and continue. Escalate only when owner-only input is genuinely required, principally proprietary source logic not available in the repository, data/broker credentials or licensing, material risk/product choices, independent-review evidence, or explicit release/live authorization.

Final acceptance is defined by `docs/DEVELOPER_HANDOFF_FINALITY.md`. Report unsupported claims as unsupported. The present architecture is advanced but is not to be described as empirically certified for real-money deployment until the stated evidence and release gates have actually passed.
