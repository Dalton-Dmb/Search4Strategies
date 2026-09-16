# AlphaIQ™ Release Modes

- **Research:** historical/offline analysis; no brokerage action.
- **Replay:** deterministic point-in-time reconstruction; no brokerage action.
- **Paper:** simulated orders/positions against historical or approved feeds.
- **Shadow:** live-like decisions/journaling without real-money order conversion.
- **Live:** explicitly authorised broker execution mode after all applicable gates.

Use the same core contracts across modes. Mode changes are configuration/release decisions, not strategy rewrites. A missing or unrecognised mode must fail safe. Credentials alone do not change mode or imply approval.
