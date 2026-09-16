# AlphaIQ™ Successor Quick Start

```bash
git clone <repository-url>
cd Search4Strategies
git checkout main
python -m pip install -r requirements.txt
python -m pytest tests/alphaiq -q
```

If the host cannot install the MT5-specific dependency, follow the repository's CI precedent for the platform-neutral AlphaIQ™ test environment rather than deleting broker-specific code.

Then read `docs/README_HANDOFF.md` and create fresh branches from current `main` for each completion slice. Do not base new completion work on old ALPHA/KPM branches without first comparing them to current main.

Before connecting data or brokers, keep credentials outside Git and use non-live/research interfaces until the corresponding release gates are satisfied.
