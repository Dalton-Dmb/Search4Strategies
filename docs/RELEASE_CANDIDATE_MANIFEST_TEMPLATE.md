# AlphaIQ™ Release Candidate Manifest Template

Complete this for every candidate release.

- Release ID:
- UTC build timestamp:
- Git commit SHA:
- CI run/reference:
- AlphaIQ™ package/version:
- Deployment mode:
- Deployment manifest fingerprint:

## Evidence lineage
- Instrument-universe version:
- Historical dataset manifest/fingerprint(s):
- Feature specification/version/fingerprint:
- Regime policy/version:
- Strategy registry versions and certification references:
- Train/validation/OOS fold manifest:
- Empirical-map policy/version:
- Statistical robustness policy/version:
- KPM-14 OOS intelligence policy/fingerprint:
- Event-context version/fingerprint:

## ML lineage (if enabled)
- Dataset/training manifest:
- Model ID/version:
- Calibration artifact:
- Champion approval reference:
- Drift baseline:

## Operational validation
- Full tests/CI: PASS / FAIL
- Point-in-time/no-lookahead validation: PASS / FAIL
- Paper/shadow validation report:
- Restart/recovery test: PASS / FAIL
- Backup/restore test: PASS / FAIL
- Health/readiness test: PASS / FAIL
- Independent audit dossier:
- Open HIGH/CRITICAL findings:

## Routing/deployment
- Broker capability configuration version:
- Canonical symbol route configuration:
- Container image digest:
- Compose/service configuration fingerprint:
- Contabo host/environment identifier (non-secret):

## Release approval
- Requested mode:
- Owner approval reference:
- Independent reviewer reference:
- LIVE gate result: BLOCKED / APPROVED

If any mandatory evidence field for the requested mode is absent, the release must fail closed rather than infer approval.
