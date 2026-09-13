# AlphaIQ™ KPM-07 — Independent Validation Audit & Research-Release Readiness

This dossier is the evidence checklist for the final Phase II research-release gate. It is deliberately separate from implementation work: the primary implementer must not be the sole certifier.

## Required independent review areas

1. Point-in-time correctness and absence of look-ahead leakage.
2. Timestamp/timezone handling and chronological replay.
3. Data-quality, stale-source and survivorship-bias review.
4. Regime labelling stability, ambiguity/UNKNOWN behavior and hysteresis.
5. Strategy-selection leakage and fold separation.
6. ML calibration, champion/challenger governance and reproducibility.
7. Out-of-sample evidence and minimum-sample discipline.
8. Journal/trace completeness and deterministic fingerprints.
9. CI status and regression coverage.
10. Research/deployment boundary: no silent real-money brokerage activation.

## Severity policy

- **CRITICAL** — can invalidate research conclusions or permit unsafe deployment behavior.
- **HIGH** — materially threatens validity, reproducibility or fail-safe behavior.
- **MEDIUM** — significant weakness requiring remediation or explicit acceptance.
- **LOW** — documentation, ergonomics or non-material robustness improvement.

Open HIGH or CRITICAL findings block research-release readiness. A final READY state also requires green CI, completed out-of-sample validation, point-in-time review, reproducibility review, journal-trace review, and an explicitly independent reviewer.

## Important limitation

Passing KPM-07 means the AlphaIQ™ research system is ready for a research release. It does **not** authorize real-money brokerage execution or autonomous capital deployment.
