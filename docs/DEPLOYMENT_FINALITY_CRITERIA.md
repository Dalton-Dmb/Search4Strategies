# AlphaIQ™ Deployment Finality Criteria

A Contabo deployment is operationally complete only when it is reproducible from a fresh host, uses an immutable/versioned application image, keeps secrets external, persists required journal/data/model state, exposes health/readiness, emits structured logs, survives/reconciles restart safely, and has tested backup/restore and rollback procedures.

Research/paper/shadow deployment can be completed before live authorisation. LIVE must additionally pass all applicable empirical, ML (if enabled), risk, execution, shadow and independent-audit gates and receive explicit owner authorisation. The package must refuse LIVE startup when required approvals/evidence are absent.

Broker routes are configuration and evidence concerns, not strategy-code forks. A successor may configure venue aliases/capabilities without changing strategy logic, but should not present example broker mappings as empirically superior until execution evidence supports them.
