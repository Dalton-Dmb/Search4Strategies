# AlphaIQ™ Handoff Glossary

- **IMPLEMENTED:** strategy code exists; not automatically certified.
- **MANIFEST_ONLY:** strategy is catalogued but exact executable approved logic is unavailable/not implemented.
- **Certified strategy:** implemented adapter that has passed required source-lineage, golden/boundary, no-lookahead, replay and approval gates.
- **OOS:** out-of-sample fold isolated from training/validation.
- **Point-in-time:** only information actually available at the decision timestamp is visible.
- **Empirical map:** performance cells separated by regime/strategy/instrument/timeframes/session/event/fold.
- **Instrument Productivity:** research score combining conservative performance and penalties under explicit weights; not a guarantee.
- **Regime mismatch:** measured deterioration between a strategy's strongest adequately sampled regime and adequately sampled outside regimes.
- **Shadow:** decisions are generated/journaled against live-like feeds without converting them into real-money orders.
- **Fail closed:** missing required evidence/configuration/approval causes abstention/blocking rather than permissive fallback.
- **Finality:** reproducible evidence, operations, audit and explicit release-mode gates described in the handoff specification.
