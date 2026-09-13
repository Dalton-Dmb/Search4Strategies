from datetime import datetime, timedelta, timezone

import pytest

from alphaiq.ml_governance import (
    DatasetManifest,
    DriftAssessment,
    EvaluationReport,
    GovernedModel,
    InMemoryGovernedModelRegistry,
    ModelStage,
    PromotionPolicy,
    ReproducibilityRecord,
    RetrainingPolicy,
    TemporalFold,
    WalkForwardPlan,
)


def dt(day: int, hour: int = 0):
    return datetime(2026, 1, day, hour, tzinfo=timezone.utc)


def manifest():
    return DatasetManifest(
        dataset_id="regime-dataset",
        version="1",
        feature_set_fingerprint="features-v1",
        label_definition_version="labels-v1",
        observation_start=dt(1),
        observation_end=dt(20),
        source_fingerprints={"XAUUSD:M15": "source-a"},
        code_version="code-v1",
        row_count=1000,
    )


def repro():
    return ReproducibilityRecord(
        random_seed=42,
        code_version="code-v1",
        environment_fingerprint="env-v1",
        dependency_fingerprint="deps-v1",
        training_command="train regime-model",
    )


def model(version="1"):
    m = manifest()
    return GovernedModel(
        model_id="regime-model",
        version=version,
        purpose="regime_classification",
        dataset_fingerprint=m.fingerprint(),
        feature_set_fingerprint=m.feature_set_fingerprint,
        hyperparameters={"depth": 3},
        reproducibility=repro(),
    )


def report(version="1", *, leakage=True, oos=True, folds=3, score=0.70, ece=0.05):
    return EvaluationReport(
        model_id="regime-model",
        model_version=version,
        dataset_fingerprint=manifest().fingerprint(),
        walk_forward_plan_version="wf-v1",
        metrics={"balanced_accuracy": score},
        calibration_metrics={"ece": ece},
        folds_evaluated=folds,
        out_of_sample=oos,
        leakage_checks_passed=leakage,
    )


def policy():
    return PromotionPolicy(
        policy_id="regime-promotion",
        version="1",
        minimum_metrics={"balanced_accuracy": 0.65},
        maximum_metrics={"calibration.ece": 0.10},
        minimum_folds=3,
        require_out_of_sample=True,
        require_leakage_checks=True,
    )


def test_dataset_manifest_fingerprint_is_deterministic():
    assert manifest().fingerprint() == manifest().fingerprint()


def test_walk_forward_rejects_insufficient_purge_gap():
    fold = TemporalFold(
        fold_id="f1",
        train_start=dt(1),
        train_end=dt(5),
        validation_start=dt(5),
        validation_end=dt(7),
        test_start=dt(8),
        test_end=dt(9),
        purge_gap=timedelta(days=1),
    )
    with pytest.raises(ValueError, match="purge gap"):
        WalkForwardPlan("wf", "1", [fold])


def test_promotion_requires_oos_leakage_and_metric_gates():
    registry = InMemoryGovernedModelRegistry()
    registry.register(model())

    with pytest.raises(ValueError, match="promotion policy failed"):
        registry.promote("regime-model", "1", report(leakage=False), policy())

    promoted = registry.promote("regime-model", "1", report(), policy())
    assert promoted.stage is ModelStage.CHAMPION
    assert registry.champion("regime_classification").version == "1"


def test_new_champion_retires_old_and_rollback_restores_it():
    registry = InMemoryGovernedModelRegistry()
    registry.register(model("1"))
    registry.promote("regime-model", "1", report("1"), policy())

    registry.register(model("2"))
    registry.promote("regime-model", "2", report("2", score=0.72), policy())
    assert registry.get("regime-model", "1").stage is ModelStage.RETIRED
    assert registry.champion("regime_classification").version == "2"

    restored = registry.rollback("regime_classification", "regime-model", "1", "post-deployment drift")
    assert restored.stage is ModelStage.CHAMPION
    assert registry.get("regime-model", "2").stage is ModelStage.ROLLED_BACK
    assert registry.champion("regime_classification").version == "1"
    assert any(event.action == "rollback_to" for event in registry.audit_log)


def test_retraining_policy_is_explicit_and_deterministic():
    drift = DriftAssessment(
        model_id="regime-model",
        model_version="1",
        feature_drift={"atr": 0.2},
        prediction_drift={},
        performance_drift={},
        threshold_breaches=["feature:atr"],
        evaluated_at=dt(20),
    )
    retraining = RetrainingPolicy(
        policy_id="retrain",
        version="1",
        retrain_on_drift=True,
        maximum_model_age=timedelta(days=30),
    )
    should_retrain, reason = retraining.decide(drift=drift, model_created_at=dt(1), as_of=dt(20))
    assert should_retrain is True
    assert reason == "drift_threshold_breached"
