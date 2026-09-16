# PR #47 / KPM-14 Technical Acceptance

Accepted scope on `main`:

- consumes the multi-dimensional empirical map;
- filters strictly to configured OOS fold;
- filters out non-IMPLEMENTED strategy specifications;
- filters cells not eligible for inference or lacking conservative expectancy;
- applies total and regime-specific sample gates;
- aggregates conservative expectancy and research metrics;
- ranks strategy/version × instrument evidence under explicit weights;
- identifies best eligible engine per instrument;
- computes preferred-regime/outside-regime degradation when both are adequately sampled;
- emits a deterministic report fingerprint.

Acceptance limitation: the module is an analytical capability. Genuine performance conclusions require real point-in-time observations generated from approved historical data and certified strategy adapters. This limitation is part of acceptance, not an unfinished defect in PR #47.
