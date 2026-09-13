# AlphaIQ™ Market Regime — Production Architecture

## Engineering doctrine

AlphaIQ™ is developed production-first. The project does not use disposable prototypes. Each increment lands permanent interfaces, schemas, validation, auditability and tests that remain valid as capabilities are activated.

The AlphaIQ™ Specification Manual is authoritative. Where a trading threshold, taxonomy, strategy mapping, event rule, model policy or risk value is not yet approved, the production surface exists but the behavior must fail safe and remain `TBD_SPEC`.

## Permanent pipeline

`Market Data -> Feature Engineering -> Regime Intelligence -> Strategy Portfolio -> Risk/Capital Allocation -> Execution -> Trade Management -> Journaling -> Analytics -> ML Feedback`

Cross-cutting production planes:

- macro/news/event context;
- model registry, calibration and drift;
- backtest and walk-forward validation;
- governance and promotion gates;
- observability, lineage and incident reconstruction.

## Current production contracts

### Market and features
`MarketSnapshot` is timezone-aware and provenance-carrying. `FeatureVector` is versioned and identifies its feature set. Future online and offline feature paths must preserve point-in-time correctness and avoid look-ahead leakage.

### Regime intelligence
`RegimeClassifier` is a common contract for deterministic and ML classifiers. `RegimeAssessment` carries probabilities/confidence, evidence, classifier identity/version, provenance and an explicit abstention state.

Current regime names are plumbing-only pending final Specification Manual approval. They do not silently encode strategy decisions.

### ML from inception
ML is a first-class subsystem now. `ModelMetadata`, model registry, calibration and drift-report contracts already exist. An ML classifier abstains unless an approved champion model exists. Approved runtime inference remains `TBD_SPEC` until the dataset, labels, features, calibration thresholds and promotion policy are ratified.

### Strategy portfolio
Strategies register their identity, version, compatible regimes, required features, contraindications and enabled status. Discovery of compatible candidates is separated from ranking and capital allocation. Until the approved routing/ranking matrix is loaded, candidates are non-executable.

### Risk
Risk is independent of strategy and ML. The default production policy is deny-by-default. ML, strategy logic and event logic can never bypass the risk policy contract.

### Execution
Execution is broker-neutral and idempotency-aware. The first adapter is simulation-only. A live broker adapter must implement the same contract and may only be enabled behind an explicit production gate.

### Journaling
Every material decision is correlated and journalable. Journal events are schema-versioned and can be written to deterministic JSON Lines or another sink. Production journal expansion will include model IDs, feature fingerprints, event context, order state transitions, fills, slippage, MAE/MFE, outcomes and promotion/governance lineage.

### Events
Macro/news/event awareness is a permanent architectural concern rather than a later bolt-on. Provider and severity contracts exist now; provider selection, event windows, surprise normalization and anomaly policy remain controlled by the Specification Manual.

## Environment progression without architectural restart

The same orchestration contracts support:

1. historical/backtest mode;
2. walk-forward validation;
3. simulation;
4. paper trading;
5. shadow trading beside production market data;
6. constrained live trading;
7. scaled live trading.

Mode-specific adapters change. Core domain contracts do not.

## Production invariants

- No look-ahead leakage.
- No hidden trading magic numbers.
- No unapproved model can trade.
- Risk retains deterministic veto authority.
- Live execution is off by default.
- All order intents have idempotency keys.
- Decisions carry model/rule/version provenance.
- Unknown or unresolved states abstain rather than guess.
- Existing Search4Strategies behavior remains backward compatible.

## Next permanent increments

The Specification Manual will authorize implementation of the final regime taxonomy and formulas, feature catalogue, regime-to-strategy matrix, strategy engines, capital allocation, risk limits, ML datasets/labels/training/promotion, event rules, broker adapters, trade management, backtest integration and monitoring thresholds. Those additions extend these contracts rather than replacing them.
