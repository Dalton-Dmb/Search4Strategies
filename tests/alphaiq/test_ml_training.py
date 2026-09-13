from datetime import timedelta

import pytest

from alphaiq.ml_training import HyperparameterSearchManifest, PointInTimeLabelSpec


def test_label_spec_fingerprint_is_stable_and_versioned():
    a = PointInTimeLabelSpec("regime", "1", timedelta(hours=4), {"method": "approved"}, True)
    b = PointInTimeLabelSpec("regime", "1", timedelta(hours=4), {"method": "approved"}, True)
    c = PointInTimeLabelSpec("regime", "2", timedelta(hours=4), {"method": "approved"}, True)
    assert a.fingerprint() == b.fingerprint()
    assert a.fingerprint() != c.fingerprint()


def test_search_manifest_requires_explicit_direction_and_trials():
    with pytest.raises(ValueError):
        HyperparameterSearchManifest("s", "1", "optuna", "loss", "sideways", {}, 42, 10)
    with pytest.raises(ValueError):
        HyperparameterSearchManifest("s", "1", "optuna", "loss", "minimize", {}, 42, 0)


def test_search_fingerprint_changes_with_search_space():
    a = HyperparameterSearchManifest("s", "1", "optuna", "loss", "minimize", {"depth": [2, 3]}, 42, 20)
    b = HyperparameterSearchManifest("s", "1", "optuna", "loss", "minimize", {"depth": [2, 4]}, 42, 20)
    assert a.fingerprint() != b.fingerprint()
