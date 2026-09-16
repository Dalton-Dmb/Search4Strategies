# AlphaIQ™ Successor — First 24 Hours

1. Clone current main and run the AlphaIQ™ test suite/CI-equivalent.
2. Read the handoff index and existing architecture documents.
3. Produce an issue-to-module map for all open KPM/ALPHA items; identify overlap before coding.
4. Search repository and owner-supplied source package for exact strategy implementations; do not infer absent rules.
5. In parallel, implement/verify KPM-15 container packaging and non-live health/recovery scaffolding because this does not depend on empirical strategy claims.
6. Establish the historical data adapter using the KPM-13 provider boundary and run a small point-in-time ingestion smoke test; then scale coverage after data quality passes.
7. Once at least one exact strategy adapter is certified and data exists, run the first end-to-end evidence slice through KPM-14 and archive the manifest/fingerprint.
8. Report blockers as concrete missing inputs, not as general requests for permission to continue.

Do not spend the first day rewriting working contracts, selecting a new framework, or training ML on synthetic/uncertified evidence.
