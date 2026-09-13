# AlphaIQ™ Research and Validation Boundary

AlphaIQ™ is developed in this repository as an auditable market-regime research, validation, replay, journaling, and paper-trading platform.

## In scope

- point-in-time market data and feature engineering
- deterministic and probabilistic regime classification
- ensemble confidence, disagreement handling, and transition persistence
- governed ML lifecycle, calibration, drift, reproducibility, and rollback metadata
- strategy registration, eligibility, scoring, and signal arbitration for research/simulation
- macro/event normalization and abnormal-market context
- deterministic replay and walk-forward validation
- decision journaling, observability, analytics, and attribution
- simulated or paper-mode adapters that cannot place real-money orders

## Outside this repository automation boundary

This environment does not implement automated real-money capital allocation, autonomous brokerage order placement, or live portfolio exposure controls. Those deployment-specific components require a separately authorized implementation and review process.

## Production design invariant

The research system must preserve the same typed contracts, provenance, idempotency concepts, feature/model versions, and audit lineage that a separately reviewed deployment adapter would consume. Research code must never silently enable a live mode.

## Fail-safe behavior

Where a deployment-only capability is absent, AlphaIQ™ must abstain, return a non-executable decision, or use a simulation/paper adapter. Missing deployment configuration must never be interpreted as permission to act.
