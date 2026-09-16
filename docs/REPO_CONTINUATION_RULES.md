# AlphaIQ™ Repository Continuation Rules

1. Branch from current `main` for new work.
2. Compare stale branches before reusing any code; do not merge them blindly.
3. Keep PRs reviewable and require CI/tests before merge.
4. Preserve backward-compatible permanent contracts unless a versioned migration is justified.
5. Every strategy/data/model/config change that affects evidence must be versioned/fingerprinted.
6. Do not weaken abstention, certification, OOS isolation, risk veto or LIVE gates to unblock a feature.
7. Prefer provider/broker adapters over hard-coded vendor logic.
8. Keep human TradingView visualisation separate from machine research/execution semantics.
9. Do not commit generated licensed raw market data unless rights explicitly permit it; manifests/fingerprints can preserve lineage.
10. Close an issue only when its stated acceptance criteria are actually met; otherwise document partial completion precisely.
