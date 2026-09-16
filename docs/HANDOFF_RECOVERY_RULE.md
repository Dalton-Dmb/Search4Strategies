# AlphaIQ™ Recovery Invariant

After process/container/VPS restart, the system must reconstruct persistent decision/journal state and applicable broker/order/position state before taking new execution actions. Idempotency keys and reconciliation must prevent duplicate intents caused by replaying startup work.

If reconciliation cannot establish a safe state, the system must abstain/block execution and surface a recoverable operational condition rather than assume no open exposure. Test this behavior in simulation/paper/shadow before any authorised live release.
