# AlphaIQ™ Handoff Test Instructions

Run the repository AlphaIQ™ tests using the same platform-neutral dependency handling as CI. The handoff adds documentation-contract tests in:

- `tests/alphaiq/test_handoff_contract.py`
- `tests/alphaiq/test_finality_status.py`

These tests intentionally verify that the handoff continues to state critical fail-closed invariants and does not falsely mark missing historical evidence, full strategy certification or LIVE authorisation as complete.
