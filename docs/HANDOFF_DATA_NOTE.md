# AlphaIQ™ Historical Data Handoff Note

The architecture deliberately does not hard-code a market-data vendor. A successor should prefer a provider with sufficient timestamp integrity, instrument/timeframe coverage and legal permission for the intended research/storage use. Provider-specific symbols must be normalised to canonical AlphaIQ™ instruments.

Do not backfill missing evidence with future-aware resampling, undocumented interpolation or synthetic prices. Gaps and session closures are observations to diagnose and report. Derived higher timeframes must have deterministic close semantics and provenance.
