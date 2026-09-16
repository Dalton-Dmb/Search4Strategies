# AlphaIQ™ Architecture — One Page

**Inputs** → historical/live-approved market observations + event context  
**Canonicalisation/data platform** → broker-neutral symbols, point-in-time bars, quality/provenance  
**Feature platform** → versioned deterministic features  
**Regime intelligence** → operational regime probabilities/evidence, hysteresis, UNKNOWN/abstention  
**Strategy research/portfolio** → only certified adapters; eligibility and arbitration  
**Instrument intelligence** → multi-asset/timeframe/session/event empirical cells  
**Risk** → independent veto/capital/exposure/execution-quality controls  
**Execution boundary** → simulation/paper/shadow and explicitly gated authorised-live adapters  
**Journal/observability** → correlated decisions, outcomes, lineage, telemetry  
**Robustness/OOS intelligence** → uncertainty, excursions, degradation, engine×instrument productivity and regime mismatch  
**ML governance** → temporal training/validation, calibration, champion/challenger, drift/rollback after clean evidence exists  
**Audit/release** → reproducibility, independent findings, release manifest, fail-closed mode gate  
**Deployment** → one versioned Contabo service package with configuration-driven brokers/instruments/modes.

The system is intentionally one architecture across research→replay→paper→shadow→authorised-live. Do not fork it into unrelated per-pair bots; empirical specialisation belongs in configuration/routing.
