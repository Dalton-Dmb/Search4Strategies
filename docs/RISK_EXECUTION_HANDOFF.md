# AlphaIQ™ Risk & Execution Successor Requirements

Reconcile, do not duplicate, the original ALPHA-005/007 requirements against current `main`.

Risk is an independent deterministic veto downstream of strategy/model selection. Policies must be explicit/versioned and fail safe when required configuration is absent. Cover portfolio/instrument/strategy exposure, drawdown/loss stops, execution-quality filters and emergency halt behavior as approved/configured. Do not hard-code aggressive historical user settings as production defaults.

Execution uses broker-neutral order/state contracts. Non-live validation must cover idempotency, duplicate intents, accepted/rejected/partial fills, stop/target lifecycle, slippage/latency telemetry, position/order reconciliation and process restart recovery. Broker adapters map canonical symbols/capabilities without embedding strategy rules.

Research/paper/shadow must remain usable without LIVE. LIVE requires an explicit release gate and owner authorisation in addition to applicable evidence/audit/risk checks.
