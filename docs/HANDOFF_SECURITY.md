# AlphaIQ™ Handoff Security Rules

- Never commit broker, market-data, VPS, database or API credentials.
- Use external secret injection/runtime environment mechanisms and least privilege.
- Keep `.env.example` non-secret.
- Do not print secrets into structured logs, manifests, test fixtures or CI output.
- Separate research/paper/shadow/live credentials and environments where supported.
- Treat release approval as data that must be explicit and verifiable, never inferred from the presence of credentials.
- Rotate credentials if exposure is suspected; do not preserve leaked values for reproducibility.
- Backups containing sensitive operational state must be access-controlled outside the public repository.
