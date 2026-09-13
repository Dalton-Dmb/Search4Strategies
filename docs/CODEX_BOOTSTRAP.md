# AlphaIQ™ Market Regime — Codex Production Contract

## Status
Production-first implementation contract for the **AlphaIQ™ Market Regime Classification Engine**.

This document is not permission to redesign the trading system. The AlphaIQ™ Specification Manual is authoritative. Where this engineering contract and the Specification Manual differ, the Specification Manual prevails.

## Core doctrine
AlphaIQ™ is built as the permanent target system from day one. There are no disposable prototypes and no planned architectural restart.

Implementation may proceed in reviewable increments, but each increment must land permanent production interfaces, schemas, lineage, validation, tests and governance seams.

## Core rule for Codex
**Do not invent trading logic.**

If a threshold, regime definition, strategy-selection rule, risk rule, feature, news/event policy, execution rule, ML policy, capital-allocation rule or broker behavior is not explicitly defined in the Specification Manual, implement the permanent configuration/interface surface and mark the unresolved behavior `TBD_SPEC`. Fail safe rather than guess.

## Product identity
Use the product name exactly as:

- **AlphaIQ™ Market Regime**
- Full technical name: **AlphaIQ™ Market Regime Classification Engine**

Use ASCII-safe identifiers such as `alphaiq` in source code.

## Permanent architecture

`Market Data -> Feature Engineering -> Regime Intelligence -> Strategy Portfolio -> Signal Arbitration -> Risk & Capital Allocation -> Execution -> Trade Management -> Journaling -> Analytics -> ML Feedback`

First-class cross-cutting subsystems from inception:

- ML dataset/model registry/inference/calibration/drift/governance;
- macro/news/economic-event context and anomaly handling;
- backtesting and walk-forward validation;
- observability, audit, telemetry and incident reconstruction;
- broker-neutral execution adapters;
- model/strategy/risk version lineage;
- deterministic safety gates and kill-switch boundaries.

## Current production increment
The branch contains the first permanent AlphaIQ™ contracts under `alphaiq/`:

- timezone-aware, provenance-carrying market snapshots;
- versioned feature vectors;
- probabilistic and abstaining regime assessments;
- deterministic and ML classifier contracts;
- model registry, calibration and drift-report contracts;
- strategy registry/selection boundary;
- deterministic risk-policy boundary;
- idempotent broker-neutral order intent/execution contracts;
- simulation execution adapter;
- schema-versioned correlated journaling;
- macro/event provider boundary;
- end-to-end orchestration through `AlphaIQEngine`;
- production invariants and tests.

## Required next implementation behavior
Continue extending the permanent architecture. Do not replace the existing contracts unless the Specification Manual requires a migration.

The same core orchestration must support historical/backtest, walk-forward, simulation, paper, shadow, constrained-live and scaled-live modes through adapters/configuration rather than separate trading engines.

## ML requirements from inception
ML is not a later bolt-on. The permanent architecture must support:

- point-in-time-correct datasets and feature lineage;
- deterministic label definitions;
- train/validation/test and walk-forward splits;
- model metadata and training-data fingerprints;
- model registry with champion/challenger state;
- calibrated probabilities;
- abstention/rejection when confidence/governance conditions fail;
- feature and prediction drift detection;
- reproducible training and inference;
- explicit promotion/rollback governance;
- no ML bypass of deterministic risk controls.

No unapproved model may influence executable trading decisions.

## Event/news requirements from inception
The architecture must support scheduled macroeconomic events, surprise values, source/version provenance, severity, pre/post-event policy, abnormal-volatility detection and historical event-response analysis. Provider choice and concrete blackout/event thresholds remain Specification-controlled.

## Risk/execution requirements
Risk is independent of strategy and ML and retains veto authority. Live execution is disabled by default until an explicit production gate is approved. Order intents must be idempotent and execution adapters must be broker-neutral.

## Journaling requirements
Every material decision must be reconstructable. Persist correlation IDs and the versions/fingerprints of data, features, classifiers/models, strategy rules, risk policies, event context and execution adapters sufficient for later audit and post-trade learning.

## Engineering standards

- Python type hints throughout public interfaces.
- Clear docstrings on public classes/functions.
- No broker credentials, secrets, tokens or account identifiers in source.
- Deterministic unit tests; no network calls in unit tests.
- Avoid global mutable state.
- Separate domain logic from MT5/broker/provider adapters.
- Dependency inversion around external data, models, news and brokers.
- No look-ahead bias.
- Timestamp/provenance explicit in time-series APIs.
- Idempotency at execution boundaries.
- Backward compatibility with Search4Strategies unless an approved migration says otherwise.

## Production invariants

1. Unknown/unresolved states abstain rather than guess.
2. No hidden trading magic numbers.
3. No unapproved model can trade.
4. Risk retains deterministic veto authority.
5. Live execution is off by default.
6. Every order intent has an idempotency key.
7. Decisions carry version/provenance lineage.
8. Backtest/paper/live share permanent domain contracts.
9. Existing Search4Strategies behavior remains intact.
10. Every PR lands permanent architecture, not throwaway scaffolding.

## Validation before promotion
No component is promoted solely because of attractive backtest performance. Promotion requires, as applicable:

- unit/integration tests;
- leakage checks;
- transaction-cost and slippage modelling;
- out-of-sample evaluation;
- walk-forward testing;
- regime-stratified metrics;
- stability/sensitivity analysis;
- calibration assessment;
- drift and rollback plan;
- reproducibility evidence;
- explicit acceptance against Specification Manual criteria.

## Standing instruction
Build all required subsystems into the permanent design now, activate them progressively, and never introduce a knowingly disposable subsystem. The AlphaIQ™ Specification Manual remains the controlling authority for exact trading, ML, event and risk behavior.
