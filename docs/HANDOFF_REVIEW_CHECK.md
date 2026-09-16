# AlphaIQ™ Handoff Review Check

Before merging the handoff PR, reviewer should confirm:

- links/filenames in `README_HANDOFF.md` resolve;
- status language does not claim missing empirical/audit/live evidence;
- PR #47 is described as complete only for its actual scope;
- no secrets or credentials appear;
- successor prompt preserves no-lookahead, certification, OOS, risk and LIVE gates;
- historical data and proprietary strategy source are identified as genuine external dependencies where absent;
- Contabo packaging is described as pending operational work, not already deployed;
- tests pass under repository CI.
