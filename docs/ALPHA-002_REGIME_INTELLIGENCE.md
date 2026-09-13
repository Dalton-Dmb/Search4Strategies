# ALPHA-002 — Regime Intelligence and Ensemble Classification

This increment establishes the permanent AlphaIQ™ regime-ensemble layer without hard-coding strategy or market thresholds that belong to the Specification/configuration layer.

## Production invariants

- Deterministic and ML classifiers remain independent evidence sources.
- Every ensemble weight and decision threshold is explicit, versioned configuration.
- No hidden confidence, margin, persistence or disagreement threshold exists in code.
- Classifier abstention is preserved; no missing source is silently converted into a vote.
- If all usable sources abstain, the ensemble returns `UNKNOWN`.
- Unknown regime labels fail safe.
- Source disagreement can be configured to force abstention.
- Confidence and runner-up margin are both checked before a regime can be accepted.
- Regime changes are subject to configurable persistence/hysteresis to reduce flip-flopping.
- Hysteresis is deterministic and resettable, so ordered replay remains reproducible.
- The full source decision trace is carried in `RegimeAssessment.evidence`.
- Feature-set lineage is preserved in assessment provenance.

## Scope boundary

This increment does not define the final AlphaIQ™ regime taxonomy or numeric production thresholds. Those remain controlled by the governing Specification Manual and approved deployment configuration. ALPHA-003 provides the production ML lifecycle used to train, validate, calibrate, promote and monitor ML regime models.
