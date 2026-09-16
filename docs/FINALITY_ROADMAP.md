# AlphaIQ™ Finality Roadmap

This is the dependency order for the successor. Parallelise where safe, but do not violate evidence dependencies.

| Stage | Work | Depends on | Exit evidence |
|---|---|---|---|
| F0 | Baseline inventory/CI | current main | recorded green baseline or documented defects |
| F1 | Exact strategy adapter integration/certification | approved source logic | certification records + tests |
| F2 | Historical provider/data activation | approved data source | quality-passed deterministic dataset manifests |
| F3 | Full point-in-time evidence replay | F1 + F2 | empirical map + robustness + OOS intelligence fingerprints |
| F4 | ML training/governance | clean labelled F3 evidence | validated challenger/champion governance artifacts |
| F5 | Pattern + DRT research integrations | approved KPM-16/17 definitions | deterministic/no-lookahead tests |
| F6 | Risk/execution reconciliation | current contracts | independent veto + lifecycle/recovery tests |
| F7 | Contabo operational packaging | F6 contracts; can begin earlier | image/compose/health/recovery/runbook CI |
| F8 | Paper/shadow validation | F1-F3 + F6-F7 | traceable validation report |
| F9 | Independent audit | evidence package | KPM-07 dossier, no blocking findings |
| F10 | Release candidate reproduction | F3-F9 as applicable | deterministic release manifest + fresh VPS reproduction |
| F11 | Deployment mode approval | owner | explicit mode approval; LIVE otherwise blocked |

The critical path to empirical credibility is **F1 → F2 → F3**. KPM-05/ML must not jump ahead of it. Contabo packaging can be developed in parallel but cannot convert missing empirical evidence into release approval.
