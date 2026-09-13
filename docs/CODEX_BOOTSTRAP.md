# AlphaIQ™ Market Regime — Production Engineering Contract

## Status
Authoritative production-first engineering contract for the **AlphaIQ™ Market Regime Classification Engine**.

This project is **not a prototype** and must not be implemented as disposable scaffolding. Every module introduced from the first commit must be designed as part of the intended production system. Development may be staged into reviewable increments, but stages are activation milestones inside one permanent architecture — never throwaway versions that are later rewritten from scratch.

The AlphaIQ™ Specification Manual is the controlling functional specification. Where this contract and the manual differ, the manual prevails.

## Prime engineering rule
**Build the target system now. Activate it progressively. Do not prototype the architecture.**

Codex must not invent trading logic. Where an approved rule is not yet numerically defined, create the production configuration surface, typed contract, validation, audit trail and tests now, and mark the unresolved parameter `TBD_SPEC`. The absence of a final number is not permission to omit the subsystem.

## Product identity
Use the human-facing product name exactly as:

- **AlphaIQ™ Market Regime**
- **AlphaIQ™ Market Regime Classification Engine**

Use ASCII-safe source identifiers such as `alphaiq`.

## Production target
AlphaIQ™ is a regime-aware, multi-strategy, machine-learning-enabled trading platform with deterministic safety controls, full journaling, model governance, event awareness, backtesting/walk-forward validation, live execution adapters, and observability.

The permanent target pipeline is:

`Market/Broker Data + Macro/News/Event Data -> Normalization -> Feature Store -> Regime Ensemble -> Strategy Portfolio -> Signal Engines -> Risk & Capital Allocation -> Execution -> Trade Management -> Journal/Event Store -> Analytics -> ML Training/Calibration/Drift -> Governance & Monitoring`

No major box in this pipeline is to be treated as a future architectural afterthought.

## Required permanent package architecture
Create or evolve toward the following production namespace without breaking existing Search4Strategies behavior:

```text
alphaiq/
  domain/              # canonical typed domain contracts
  config/              # validated hierarchical configuration
  data/                # market/broker/event ingestion and normalization
  features/            # feature computation, provenance, leakage controls
  regime/              # deterministic + ML + ensemble regime classification
  strategies/          # registry and production strategy engines/adapters
  signals/             # canonical signal contracts and arbitration
  portfolio/           # strategy allocation and portfolio constraints
  risk/                # pre-trade, intraday, portfolio and kill-switch controls
  execution/           # broker-neutral execution contracts/adapters
  trade_management/    # stops, targets, trailing, partials, lifecycle state
  journal/             # immutable structured decision/trade event records
  analytics/           # KPIs, attribution, regime/strategy diagnostics
  ml/                  # datasets, training, inference, calibration, registry, drift
  events/               # macro calendar/news/anomaly interfaces and policies
  backtest/             # event-driven simulation and realistic costs
  validation/           # walk-forward, purged CV, robustness/stress testing
  governance/           # approvals, model/version lineage, promotion gates
  observability/        # logs, metrics, health, alerts
  adapters/             # MT5 and other external integrations
```

The exact internal file split may differ if justified, but these production responsibilities must exist from inception as explicit modules/contracts.

## 1. Canonical domain model
Implement production-grade typed contracts for at least:

- MarketSnapshot / Bar / Tick / SessionContext
- FeatureVector and FeatureProvenance
- EventContext / NewsEvent / MacroEvent
- RegimeAssessment and RegimeDistribution
- StrategyDefinition / StrategyCandidate / StrategyDecision
- Signal / SignalEvidence / SignalConflict
- PortfolioAllocation
- RiskDecision / RiskVeto / RiskBudget
- OrderIntent / ExecutionReport / PositionState
- TradeIntent / TradeLifecycleEvent
- JournalEvent / DecisionTrace
- ModelArtifact / ModelVersion / InferenceResult / DriftReport

All records must support timestamp, source/provenance, schema version and deterministic serialization where relevant.

## 2. Regime engine — deterministic + ML from day one
The regime subsystem must be architected immediately as an ensemble-capable production service, not a rule shell waiting for ML later.

Required classifier contract:

```python
classify(snapshot, features, event_context=None) -> RegimeAssessment
```

Provide production interfaces for:

- deterministic/rule classifier;
- supervised ML classifier;
- unsupervised/latent-state classifier where later approved;
- ensemble/fusion classifier;
- confidence calibration;
- abstention/UNKNOWN behavior;
- regime transition/hysteresis handling;
- model/version provenance.

The ML interfaces, dataset contracts, model registry abstractions, training/inference separation and calibration hooks must be implemented now. Actual models may initially be untrained until approved data and labels are available, but ML is a first-class subsystem from the outset.

No ML component may bypass deterministic risk controls.

## 3. Regime taxonomy
Use the Specification Manual's approved taxonomy as it is finalized. Until every final label is codified, support extensible registry-based labels and a mandatory `UNKNOWN`/`UNCLASSIFIED` state.

Do not collapse direction, volatility and state transition into one crude enum if the manual defines a multidimensional regime representation. The architecture must support hierarchical or multi-axis regime state.

## 4. Feature platform
Build a production feature layer with:

- explicit lookback windows;
- timestamp and source provenance;
- no-lookahead guarantees;
- train/live parity;
- missing-data policy;
- normalization/scaling versioning;
- session/timezone handling;
- feature-set version identifiers;
- deterministic reproducibility.

It must accommodate price/volume/volatility, structure, momentum, trend, mean-reversion, liquidity, session, cross-asset/intermarket and external-event features when approved.

## 5. Strategy portfolio
Do not model the system as one strategy selected from a toy registry. Build a production strategy portfolio architecture capable of supporting the complete approved AlphaIQ™ strategy library, including trend, breakout, momentum, range/mean-reversion and other strategies identified in the manual.

Each strategy must declare:

- strategy/version ID;
- compatible and contraindicated regimes;
- required features/data;
- entry/exit contract;
- risk assumptions;
- session/instrument constraints;
- cooldown/conflict behavior;
- enablement and approval status.

The strategy selector/arbitrator must support multiple eligible strategies, ranking, conflicts, allocation and abstention. No mapping may be fabricated where the manual is silent.

## 6. Risk and capital allocation
Risk is a permanent independent control plane from day one.

Build interfaces and production enforcement points for:

- per-trade risk;
- instrument and portfolio exposure;
- correlation/concentration limits;
- leverage/margin safeguards;
- daily/weekly drawdown limits;
- consecutive-loss controls;
- volatility/event risk throttling;
- max concurrent positions;
- liquidity/spread/slippage constraints;
- kill switch / circuit breaker;
- stale-data / broker-disconnect veto;
- strategy and model risk budgets.

Unresolved numerical values remain validated configuration marked `TBD_SPEC`; the subsystem itself is not deferred.

## 7. Execution and trade management
Implement broker-neutral production contracts immediately for:

- market/limit/stop order intent;
- idempotency/client order IDs;
- acknowledgement, rejection and partial fills;
- slippage and transaction-cost capture;
- retry policy boundaries;
- reconciliation with broker truth;
- position state machine;
- stop loss, target, trailing, breakeven and partial-close lifecycle;
- emergency flatten/kill-switch behavior.

No live account execution should be enabled merely by building these interfaces. Live trading must require an explicit production configuration gate and later approval. Paper/simulation mode must use the same contracts.

## 8. Journaling as system of record
Journaling is mandatory infrastructure, not an add-on.

Every material decision must be reconstructable:

`data -> features -> regime -> strategy eligibility -> signal -> risk decision -> order -> fill -> management -> exit -> outcome`

Journal/event records must include schema version, component/model versions, configuration fingerprint, evidence, timestamps and correlation IDs. Design for immutable append-only storage with export to analytical stores.

## 9. ML platform and model governance
Implement the production ML lifecycle architecture now:

- dataset definitions and snapshots;
- leakage-safe label generation;
- train/validation/test separation;
- walk-forward and purged/embargoed validation hooks;
- feature/model version lineage;
- experiment metadata;
- model registry abstraction;
- calibration metrics;
- inference service contract;
- champion/challenger support;
- drift detection;
- rollback;
- promotion approval gates;
- shadow mode before production activation.

Model training can proceed as soon as approved datasets/labels exist; it is not relegated to a later architectural rewrite.

Avoid reinforcement learning unless the Specification Manual expressly authorizes it and defines the safety/evaluation framework.

## 10. External news, macro and abnormal-event layer
Treat events as a first-class data source now. Build decoupled interfaces for economic calendar, scheduled macro releases, news/event sentiment or classification, market-shock/anomaly detection and event-risk policies.

The system must be capable of learning/encoding how historically abnormal conditions affect regime confidence, risk throttles and strategy eligibility, subject to the Specification Manual and data-quality requirements.

External providers must sit behind adapters; domain logic must not depend directly on one vendor.

## 11. Backtesting and validation
The production engine and research engine must share the same domain logic wherever practicable to avoid research/live divergence.

Provide architecture for:

- event-driven simulation;
- realistic spread, commission, slippage and latency assumptions;
- walk-forward testing;
- purged/embargoed time-series CV where ML applies;
- Monte Carlo/bootstrapped robustness testing;
- parameter stability;
- regime-specific performance attribution;
- strategy interaction/portfolio tests;
- out-of-sample promotion gates;
- reproducible run manifests.

## 12. Observability and operations
Build production seams for:

- structured logs;
- metrics;
- health checks;
- data freshness;
- execution reconciliation;
- model/regime confidence monitoring;
- strategy/risk state;
- alerts;
- incident-safe shutdown and restart.

No secrets, broker credentials or account identifiers may be committed to source.

## 13. Configuration
All behavior must be controlled through validated, versioned configuration with clear defaults only where the specification authorizes defaults.

Production, paper, backtest and development environments must be separated. A configuration fingerprint must be included in journal/backtest records.

## 14. Engineering quality gates
From the first implementation:

- typed public interfaces;
- deterministic unit tests;
- integration tests for subsystem boundaries;
- no network access in unit tests;
- dependency inversion for external services;
- no global mutable trading state;
- explicit state machines where lifecycle matters;
- idempotency for execution-sensitive operations;
- fail-closed behavior for stale/invalid/missing critical data;
- backwards compatibility with existing Search4Strategies until an explicit migration is approved;
- no hidden magic numbers;
- no look-ahead bias;
- no silent exception swallowing in trading/risk/execution paths.

## 15. Production-first implementation sequence
Codex may implement in small PRs, but each PR must land permanent architecture. Suggested sequence:

1. Domain contracts, configuration, event/journal backbone, architecture tests.
2. Data normalization + feature provenance layer.
3. Deterministic regime engine + ML dataset/inference/model-registry contracts + ensemble shell.
4. Full strategy registry/portfolio/selector contracts and approved strategy implementations.
5. Independent risk/capital-allocation control plane.
6. Execution + position/trade-management state machines in simulation/paper mode.
7. Backtest/walk-forward/ML validation integration.
8. Initial ML regime models, calibration and champion/challenger workflow.
9. Macro/news/anomaly adapters and event-risk integration.
10. Observability, operational hardening, reconciliation and guarded live-trading readiness.

This sequence is **not** permission to postpone architecture. It is the order in which complete production modules become executable.

## Immediate Codex task
Begin implementing the permanent production architecture on branch `alphaiq-market-regime`.

For the first PR, implement enough of every core subsystem's contract to make the system architecture concrete and testable, while fully implementing the domain/config/journal backbone and the first end-to-end dry-run path:

`MarketSnapshot -> Features -> RegimeAssessment -> StrategyDecision -> RiskDecision -> OrderIntent -> simulated ExecutionReport -> Journal trace`

The dry-run path must use production contracts and adapters, not disposable mocks as application architecture. Test doubles are acceptable only inside tests.

Also implement ML production contracts in this first PR: dataset specification, model metadata/version, classifier protocol, inference result, registry interface, calibration interface and drift-report contract. If there is no approved trained model yet, inference must explicitly abstain rather than invent predictions.

## First-PR acceptance criteria

- Existing Search4Strategies behavior/tests remain intact.
- Permanent `alphaiq` architecture exists for all target subsystems.
- A deterministic end-to-end dry run traverses the canonical pipeline without placing a live order.
- ML is represented as a real first-class production subsystem, not a `future/` placeholder.
- Journal trace can reconstruct the full dry-run decision chain.
- Risk can independently veto an otherwise valid strategy/signal.
- Execution state is broker-neutral and idempotency-aware.
- Unspecified trading thresholds are configuration/TBD_SPEC, never fabricated.
- Unit + integration tests pass.
- Architecture document identifies no planned throwaway subsystem.
- Codex lists all unresolved specification dependencies explicitly.

## Definition of done for the project
AlphaIQ™ is not complete merely because code runs. Production readiness requires, at minimum:

- approved regime taxonomy and strategy matrix implemented;
- validated deterministic and ML regime components;
- full approved strategy library;
- tested portfolio/risk controls;
- realistic costs and out-of-sample validation;
- journal/audit completeness;
- model governance/drift controls;
- event/news risk integration where specified;
- broker reconciliation and guarded execution;
- observability/incident controls;
- paper/shadow qualification before live activation;
- explicit release/promotion checklist and rollback path.

The architecture must reach these requirements by extension and configuration of the system started today — **not by replacing a prototype later**.
