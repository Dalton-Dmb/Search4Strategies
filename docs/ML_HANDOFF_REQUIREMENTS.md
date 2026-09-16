# AlphaIQ™ ML Successor Requirements

ML work is downstream of clean point-in-time evidence. Preserve the existing lifecycle/governance contracts and use ML for regime/meta-selection under explicit governance, not as an unconstrained trade generator.

A production candidate must record dataset/fold/training manifests, feature and label versions, hyperparameters, calibration artifact, temporal/purged walk-forward results, confusion/abstention diagnostics, OOS metrics by regime/instrument where statistically supportable, champion/challenger decision, drift baseline, retraining policy and rollback target.

Prevent leakage from future bars, overlapping labels/folds and post-outcome features. Failed calibration, insufficient samples or unresolved drift should abstain/block promotion according to policy rather than be overridden manually in code.
