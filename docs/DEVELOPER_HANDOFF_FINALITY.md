# AlphaIQ™ Market Regime — Developer Handoff to Finality

**Repository:** `Dalton-Dmb/Search4Strategies`  
**Handoff baseline:** `main`, after merged PR #47 (KPM-14)  
**Purpose:** enable a competent successor developer/agent to complete, validate, package and deploy AlphaIQ™ without redesigning the system or inventing missing trading rules.

## 1. Product mandate

AlphaIQ™ Market Regime is a production-first, broker-neutral, multi-instrument, multi-timeframe trading research and decision architecture. The full technical designation is **AlphaIQ™ Market Regime Classification Engine**.

It shall not be instrument-centric or fixed-timeframe-centric. It shall evaluate a configurable universe of instruments across hierarchical timeframes and select strategies, instruments and execution timeframes conditional on the prevailing market regime and empirically validated performance.

Gold is deliberately prioritised, not exclusive. The research universe includes XAUUSD, XAUGBP, XAUEUR, XAUJPY and configurable additional Gold crosses, together with liquid FX such as USDJPY, USDCHF, EURCHF, EURUSD, GBPUSD, NZDUSD, AUDUSD, USDCAD, GBPJPY and others.

Timeframe hierarchy is context/regime D1→H4→H1; H1 is the primary thesis/operating timeframe; M30/M15 refine execution; M5 is used only where a strategy genuinely requires it. Strategy adapters declare their own timeframe graph.

## 2. Architectural invariants — DO NOT REMOVE

1. No look-ahead. A higher-timeframe observation is unavailable until its bar is closed.
2. Unknown/insufficient regime evidence abstains.
3. MANIFEST_ONLY or uncertified strategy logic cannot generate executable empirical evidence.
4. ML is not an unconstrained signal generator; it is governed, calibrated, reproducible and subject to champion/challenger controls.
5. Risk controls are independent vetoes and cannot be overridden by strategy/model confidence.
6. Canonical instruments are independent of broker-specific symbol names.
7. Research, replay, paper, shadow and authorised-live modes share permanent contracts.
8. LIVE must fail closed until explicit release approval and all required safety/audit gates pass.
9. Every decision and outcome must preserve dataset, feature, strategy, regime, model, configuration and code lineage.
10. No credentials or secrets in source control.
11. Do not invent proprietary strategy formulas, thresholds or mappings. Missing approved logic must abstain and remain explicitly incomplete.
12. Production deployment does not itself constitute authorisation to trade real money.

## 3. What is already implemented

The repository contains the permanent AlphaIQ™ architecture and successive KPM milestones, including:

- Core domain/contracts, fail-safe pipeline, journal, event and execution abstractions.
- Point-in-time market-data and feature platform with replay and provenance.
- Regime intelligence ensemble with confidence/margin gates, disagreement handling, transitions and hysteresis.
- ML lifecycle/governance: temporal validation, purged walk-forward contracts, calibration, model lineage, champion/challenger, drift/retraining/rollback governance.
- Strategy portfolio registration and arbitration with explicit FLAT/NO_TRADE behavior.
- Operational regime labelling: Strong Trend, Weak Trend, Range/Mean Reversion, Compression, Expansion, Transition, Event Shock and Chop.
- Research strategy catalogue and adapter boundary.
- Regime×strategy performance matrix with sample gates and conservative confidence-bound ranking.
- Event/abnormal-market research context.
- Shadow-validation ledger and independent-audit readiness gate.
- Multi-instrument empirical map and broker-neutral instrument universe.
- Historical data-lake contracts, dataset quality checks, deterministic fingerprints and train/validation/OOS fold lineage.
- Statistical robustness diagnostics: explicit annualisation policy, bootstrap confidence intervals, Sharpe/Sortino/Calmar-like diagnostics, CVaR, drawdown, MFE/MAE and OOS degradation.
- Strategy-adapter certification gate requiring source reference, golden/boundary tests, no-lookahead verification, deterministic replay and owner approval.
- Broker specialisation/deployment routing contracts with LIVE fail-closed semantics.
- KPM-13 historical provider boundary and point-in-time multi-timeframe snapshots.
- KPM-14 OOS-only instrument productivity and regime-mismatch intelligence. Train/validation evidence is excluded from the OOS leaderboard; uncertified strategies are excluded; inadequately sampled cells are excluded; output is deterministically fingerprinted.

PR #47 is therefore **complete as a merged KPM-14 implementation**. The remaining work is project completion beyond #47, not unfinished code inside #47.

## 4. Known open completion work

### A. Exact strategy-source integration / KPM-10

The certification machinery exists, but proprietary/approved engines must remain MANIFEST_ONLY until their exact source logic is present. Repository code search at handoff found no exact `SpotOn` or `RRRB` source implementation on `main`. Do not reverse-engineer or guess these rules merely to make tests green.

Target strategy families include Range/Mean Reversion, trend continuation, breakout/expansion, reversal/transition, RRRB/RRRS, UtBMachine, Trinity Steps, SpotOn, Golden Goose/SMT and Unicorn.

For each exact source obtained: implement an adapter; declare required features and timeframe graph; preserve deterministic/non-repainting semantics; add golden cases, boundaries, no-lookahead and deterministic replay tests; record source/version lineage; then obtain owner approval before certification.

### B. Genuine empirical evidence activation / KPM-13 onward

Connect a real historical provider or owner-supplied historical files to the existing provider-neutral contracts. Required data must be timestamped, canonicalised, quality-checked and sufficiently deep across the Gold-priority and FX universe. Generate D1/H4/H1/M30/M15 and M5 only where required. Preserve point-in-time closure semantics.

Run the full pipeline: historical bars → canonical observations → point-in-time feature snapshots → operational regime labels → certified strategy adapters → outcomes/MFE/MAE/execution assumptions → train/validation/OOS folds → empirical map → KPM-12 robustness diagnostics → KPM-14 OOS productivity/mismatch report.

No claim of historical profitability or robustness is permitted until this run exists and its manifests/fingerprints are archived.

### C. ML training / KPM-05

Do not train the production regime/meta-model merely because the interfaces exist. Training begins only after a clean labelled point-in-time dataset exists. Use purged walk-forward validation, calibration diagnostics, confusion matrices, abstention analysis, reproducible manifests, champion/challenger governance and drift baselines. Promotion requires the existing governance gates; no unapproved champion.

### D. Contabo production packaging / KPM-15

Complete the operational portion of the deployment architecture:

- production Dockerfile/image;
- compose/service orchestration;
- non-secret `.env` template and external secret injection;
- persistent journal/model/data volumes;
- health and readiness checks;
- structured logs;
- restart/recovery and idempotent reconciliation;
- deterministic deployment manifest;
- backup/restore, upgrade and rollback procedure;
- CI packaging/configuration checks;
- Contabo VPS installation/runbook.

Deployment modes must include research, paper and shadow. LIVE startup remains blocked until explicit release approval plus required risk, evidence and audit gates are present.

### E. Pattern engine / KPM-16

Integrate approved definitions for double top/bottom, head-and-shoulders/inverse, triangles, wedges, flags, pennants and cup-and-handle where exact definitions exist. Machine adapters should emit deterministic pattern state/geometry/neckline or breakout coordinates/evidence/invalidation. Pine visualization is separate and may draw human navigation aids. Require confirmed pivots, no repainting/look-ahead and abstention on ambiguous geometry.

### F. DRT / Box Theory / KPM-17

Integrate approved DRT/session/day range concepts as regime/context features. Preserve distinction between contemporary session/day range parameters and weekly/monthly extremes. Support session calendars/timezones, breakout/rejection/range-location features and missing-bar diagnostics. Where a full 24-hour market definition applies, preserve the expected 96 M15 bars/day and diagnose unexplained gaps rather than normalising a 92-bar observation.

### G. Risk and execution completion

Reconcile the original ALPHA-005 risk-control and ALPHA-007 execution requirements against current `main`; implement from a fresh branch, not stale historical branches. Risk must remain a deterministic independent veto. Execution contracts must support simulation/paper/shadow and only explicitly authorised live adapters, with idempotency, state reconciliation, partial/rejected fills, latency/slippage capture, position reconciliation and restart recovery.

## 5. Empirical acceptance matrix

The production evidence key is:

`Regime × Strategy × Instrument × Thesis-TF × Entry-TF × Session × Event-State × Fold`

For adequately sampled OOS cells, report at minimum expectancy and confidence bounds, win rate, payoff ratio, Profit Factor, max/average drawdown, explicit per-trade vs annualised Sharpe/Sortino semantics, Calmar where meaningful, MFE, MAE, MFE/MAE ratio, capture efficiency, tail/CVaR diagnostics, slippage, latency, sample size, OOS stability and train→validation→OOS degradation.

KPM-14's productivity score is a research prioritisation device, not proof of future returns. Regime-mismatch degradation must remain visible so the router can learn where a strategy deteriorates outside its preferred environment.

## 6. Instrument and broker intelligence

Keep canonical symbol identity separate from venue aliases. The architecture must permit empirical specialisation such as XAUUSD→one broker, USDJPY→another, EURCHF→another, without modifying strategy code. Venue choice must ultimately be supported by evidence including availability, spread, slippage, fill quality and observed strategy performance; examples in tests/configuration are not recommendations or hard-coded mandates.

## 7. Release gates before deployment

A successor must not describe AlphaIQ™ as production-validated until all applicable gates are evidenced. Required sequence:

1. CI and full test suite green.
2. Exact strategy adapters certified; MANIFEST_ONLY engines cannot contaminate empirical claims.
3. Genuine historical datasets pass quality/lineage checks.
4. Purged walk-forward train/validation/OOS evaluation completed.
5. OOS empirical map and KPM-14 report archived with deterministic fingerprints.
6. ML candidate validation and governance completed if ML is enabled.
7. Paper/shadow validation completed with journal traceability.
8. Independent reviewer completes the KPM-07 audit dossier and no blocking HIGH/CRITICAL findings remain.
9. Risk and execution recovery tests pass.
10. Contabo package passes health, restart, backup and rollback tests.
11. Owner explicitly authorises the intended release mode. LIVE remains off otherwise.

## 8. Required successor deliverables

Deliver one coherent release rather than a rewrite:

- completed source tree and tests;
- certified strategy-adapter registry with evidence references;
- historical dataset/evidence-run manifests (not necessarily raw licensed data in Git);
- OOS empirical and regime-mismatch reports;
- ML model card/governance record if ML is enabled;
- paper/shadow validation report;
- independent audit dossier;
- Docker/compose package and Contabo runbook;
- broker capability/routing configuration;
- operations guide covering startup, shutdown, health, logs, backup, recovery, upgrade and rollback;
- final release manifest containing code commit, config versions, dataset fingerprints, feature versions, strategy versions, regime policy, model versions and audit/release approvals.

## 9. Master implementation instruction for the successor developer

> Continue AlphaIQ™ from the current `main` branch. Treat the repository contracts and this handoff as authoritative. Do not redesign the system into a single-instrument, single-timeframe or single-broker bot. Preserve point-in-time/no-lookahead semantics, deterministic lineage, abstention, certification, OOS isolation, independent risk vetoes and fail-closed LIVE controls. First inventory current code/issues/tests and reconcile rather than duplicate existing modules. Import exact approved strategy sources; never invent missing proprietary logic. Connect genuine historical data through the existing provider boundary, execute the complete evidence pipeline, generate reproducible OOS/regime-mismatch intelligence, and only then train/govern ML. Complete KPM-15/16/17, risk/execution reconciliation, paper/shadow validation, independent audit evidence and Contabo packaging. Work in small reviewable PRs with tests and CI, but deliver a single coherent release candidate. Never hard-code credentials or silently authorise real-money execution. A deployment is acceptable only when its release manifest is reproducible and all required gates pass.

## 10. Definition of finality

AlphaIQ™ reaches engineering finality for this phase when a fresh Contabo VPS can be provisioned from documented instructions; the same versioned package can ingest approved market/event data, reconstruct point-in-time features, classify regimes, run only certified strategies, journal every decision, produce OOS and shadow evidence, enforce independent risk controls, recover safely after restart, and expose operational health; an independent reviewer can reproduce the evidence from manifests; and the owner can explicitly select an authorised deployment mode without code changes.

Until the historical evidence, strategy certification and audit gates are actually completed, the system is **architecturally advanced but not empirically certified for real-money deployment**. This distinction is mandatory in all successor reporting.
