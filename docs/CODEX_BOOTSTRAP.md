# AlphaIQ™ Market Regime — Codex Bootstrap Contract

## Status
Engineering bootstrap for the **AlphaIQ™ Market Regime Classification Engine**.

This document is an implementation contract, not permission to redesign the trading system. The forthcoming AlphaIQ™ Specification Manual is authoritative. Where this bootstrap document and the later manual differ, the later manual prevails.

## Core rule for Codex
**Do not invent trading logic.**

If a threshold, regime definition, strategy-selection rule, risk rule, model feature, news/event policy, execution rule, or broker-specific behavior is not explicitly defined in the specification, expose it as configuration or a typed interface and mark it `TBD_SPEC`. Do not silently choose a value.

## Immediate objective
Create a production-grade architectural foundation inside the existing `Search4Strategies` codebase for a regime-aware trading system without changing or breaking the current discovery engine.

The first milestone is **architecture + contracts + tests**, not live trading and not model optimization.

## Product identity
Use the product name exactly as:

- **AlphaIQ™ Market Regime**
- Full technical name when appropriate: **AlphaIQ™ Market Regime Classification Engine**

The `™` symbol belongs in human-facing documentation and UI text. Use ASCII-safe Python/package/module identifiers in source code, e.g. `alphaiq`.

## Architectural intent
The completed system is expected to evolve toward this pipeline:

`Market Data -> Feature Engineering -> Market Regime Classification -> Strategy Selection -> Signal Engines -> Risk Engine -> Execution -> Trade Management -> Journaling -> Performance Analytics -> ML Feedback`

A later external-factors layer may incorporate scheduled macroeconomic events, news, and historically abnormal market behavior. That layer must remain optional and decoupled from the deterministic core.

## Milestone 0 — required implementation

Create a new package namespace that does not disturb current `app` behavior:

```text
alphaiq/
  __init__.py
  domain/
    __init__.py
    enums.py
    models.py
  regime/
    __init__.py
    base.py
    rule_based.py
  strategy/
    __init__.py
    registry.py
    selector.py
  risk/
    __init__.py
    policy.py
  journal/
    __init__.py
    models.py
    sink.py
  config/
    __init__.py
    schema.py
```

Add tests under `tests/alphaiq/`.

### 1. Typed domain model
Implement typed, testable contracts for:

- `MarketSnapshot`
- `FeatureVector`
- `RegimeAssessment`
- `StrategyCandidate`
- `StrategyDecision`
- `RiskDecision`
- `TradeIntent`
- `JournalEvent`

Prefer Python dataclasses or Pydantic only if the existing dependency footprint makes that appropriate. Avoid adding heavy dependencies without necessity.

### 2. Regime abstraction
Define a `RegimeClassifier` protocol/ABC with a deterministic method conceptually equivalent to:

```python
classify(snapshot: MarketSnapshot, features: FeatureVector) -> RegimeAssessment
```

`RegimeAssessment` must support:

- a machine-readable regime label;
- confidence/probability where available;
- evidence/features supporting the decision;
- classifier/version identifier;
- timestamp/data provenance;
- an explicit `UNKNOWN` / `UNCLASSIFIED` outcome.

### 3. Regime labels
Do **not** freeze the final AlphaIQ™ taxonomy yet. Provide an extensible enum/registry with only safe provisional categories required for plumbing, including at minimum:

- `UNKNOWN`
- `TRENDING`
- `RANGING`
- `TRANSITIONAL`
- `HIGH_VOLATILITY`

Mark these as provisional in documentation. Do not infer trading direction or strategy from these labels yet.

### 4. Rule-based classifier skeleton
Implement a rule-based classifier shell that accepts externally supplied configuration/rules. It may validate inputs and return `UNKNOWN` when no approved rules are configured.

**It must not embed arbitrary ADX, ATR, EMA, RSI, volatility, session, or structure thresholds.** Those will come from the AlphaIQ™ Specification Manual.

### 5. Strategy registry and selector
Create a strategy registry that allows named strategy engines to declare:

- strategy ID/name;
- compatible regime(s);
- required features;
- optional contraindications;
- version;
- enabled/disabled status.

The selector must be deterministic and auditable. Until the approved regime-to-strategy matrix is supplied, it must return no executable strategy when the mapping is absent.

### 6. Risk boundary
Create a `RiskPolicy` interface. No live risk percentages, leverage, position sizing, stop placement, daily-loss limits, or trade-frequency rules are to be hard-coded at this milestone.

### 7. Journal-first design
Every classification and selection decision must be capable of producing a structured journal event containing enough evidence to reconstruct **why** the system made or declined a decision.

Journal records should be serializable and include schema versioning.

### 8. ML boundary
Create interfaces that allow a future ML classifier to implement the same regime contract as the deterministic classifier.

Do not train a model in Milestone 0.
Do not add reinforcement learning.
Do not let an ML component bypass deterministic risk controls.

### 9. Backward compatibility
- Existing `Search4Strategies` commands must continue to run unchanged.
- Existing tests must continue to pass.
- New AlphaIQ™ modules must initially be additive.

## Engineering standards

- Python type hints throughout public interfaces.
- Clear docstrings on public classes/functions.
- No broker credentials, secrets, tokens, or account identifiers in source.
- Deterministic tests; no network calls in unit tests.
- Avoid global mutable state.
- Separate domain logic from MT5/broker adapters.
- Prefer dependency inversion around external data/news/broker services.
- No look-ahead bias in any future market-data transformation.
- Any time-series feature API introduced now must make timestamp/provenance explicit.

## Required tests
At minimum add tests proving:

1. A classifier can return `UNKNOWN` safely when rules are unavailable.
2. `RegimeAssessment` preserves label, confidence/evidence, version, and provenance.
3. Strategy selection refuses to manufacture a strategy where no approved mapping exists.
4. Disabled strategies cannot be selected.
5. Journal events serialize deterministically.
6. Risk interface can veto a trade intent.
7. Existing application imports/CLI remain unaffected.

## Deliverables for the first PR

- New AlphaIQ™ package skeleton.
- Domain contracts and provisional enums.
- Rule-based classifier shell.
- Strategy registry + safe selector.
- Risk policy interface.
- Journal schema/sink interface.
- Unit tests.
- `docs/ALPHAIQ_ARCHITECTURE.md` explaining module boundaries and extension points.
- No live-order execution.
- No arbitrary trading thresholds.

## Definition of done
The milestone is complete only when:

- all existing tests pass;
- all new AlphaIQ™ tests pass;
- current Search4Strategies behavior is not broken;
- there are no hidden magic numbers defining trading behavior;
- unspecified trading rules are explicitly identified as `TBD_SPEC` or configuration;
- the architecture can accept both deterministic and ML regime classifiers behind the same contract;
- every classification/strategy decision is designed to be journalable and auditable.

## Subsequent milestones (do not implement yet)

1. Final regime taxonomy and mathematical definitions.
2. Market feature catalogue and provenance rules.
3. Approved regime-to-strategy matrix, including genuine range/mean-reversion handling.
4. Strategy engine adapters.
5. Risk and capital-allocation engine.
6. Backtest/walk-forward framework integration.
7. ML regime classifier and calibration.
8. News/event anomaly layer.
9. Execution/broker adapters.
10. Continuous journaling, analytics, drift monitoring, and model governance.

Codex should stop at Milestone 0 unless a later AlphaIQ™ specification or issue explicitly authorizes more.