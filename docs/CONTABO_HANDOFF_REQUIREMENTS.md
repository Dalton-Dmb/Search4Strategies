# AlphaIQ™ Contabo Successor Requirements

Target a standard supported Linux VPS and keep deployment infrastructure portable. The successor must document prerequisite packages, firewall/network assumptions, filesystem/volume layout, service user/permissions, secret injection, container build/pull, initialisation, health verification, logs, controlled shutdown/startup, upgrade, rollback, backup and restore.

Use a restart policy that does not bypass application-level reconciliation. Persistent state must not disappear when the application container is replaced. Health/readiness must distinguish process-alive from safe-to-serve. A LIVE configuration that lacks the release/audit/risk evidence gate must terminate/refuse live activation rather than degrade silently.

The runbook must contain a fresh-host reproduction test and a rollback drill. Host credentials, broker credentials and data-provider secrets are supplied out-of-band and never committed.
