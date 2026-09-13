from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence


class ModelStage(str, Enum):
    CHALLENGER = "challenger"
    CHAMPION = "champion"
    RETIRED = "retired"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class DatasetManifest:
    dataset_id: str
    version: str
    feature_set_fingerprint: str
    label_definition_version: str
    observation_start: datetime
    observation_end: datetime
    source_fingerprints: Mapping[str, str]
    code_version: str
    row_count: int
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.observation_start.tzinfo is None or self.observation_end.tzinfo is None:
            raise ValueError("dataset timestamps must be timezone-aware")
        if self.observation_end < self.observation_start:
            raise ValueError("observation_end must be >= observation_start")
        if self.row_count < 1:
            raise ValueError("row_count must be >= 1")

    def fingerprint(self) -> str:
        payload = {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "feature_set_fingerprint": self.feature_set_fingerprint,
            "label_definition_version": self.label_definition_version,
            "observation_start": self.observation_start.astimezone(timezone.utc).isoformat(),
            "observation_end": self.observation_end.astimezone(timezone.utc).isoformat(),
            "source_fingerprints": dict(sorted(self.source_fingerprints.items())),
            "code_version": self.code_version,
            "row_count": self.row_count,
            "extra": dict(sorted(self.extra.items())),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class TemporalFold:
    fold_id: str
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    test_start: datetime
    test_end: datetime
    purge_gap: timedelta

    def validate(self) -> None:
        values = [
            self.train_start,
            self.train_end,
            self.validation_start,
            self.validation_end,
            self.test_start,
            self.test_end,
        ]
        if any(value.tzinfo is None for value in values):
            raise ValueError("fold timestamps must be timezone-aware")
        if self.purge_gap < timedelta(0):
            raise ValueError("purge_gap must be non-negative")
        if self.train_end < self.train_start:
            raise ValueError("invalid train window")
        if self.validation_end < self.validation_start:
            raise ValueError("invalid validation window")
        if self.test_end < self.test_start:
            raise ValueError("invalid test window")
        if self.validation_start - self.train_end < self.purge_gap:
            raise ValueError("train/validation purge gap violated")
        if self.test_start - self.validation_end < self.purge_gap:
            raise ValueError("validation/test purge gap violated")


@dataclass(frozen=True)
class WalkForwardPlan:
    plan_id: str
    version: str
    folds: Sequence[TemporalFold]

    def __post_init__(self) -> None:
        if not self.folds:
            raise ValueError("walk-forward plan requires at least one fold")
        for fold in self.folds:
            fold.validate()
        ordered = sorted(self.folds, key=lambda f: f.test_start)
        if list(self.folds) != ordered:
            raise ValueError("folds must be ordered by test_start")


@dataclass(frozen=True)
class EvaluationReport:
    model_id: str
    model_version: str
    dataset_fingerprint: str
    walk_forward_plan_version: str
    metrics: Mapping[str, float]
    calibration_metrics: Mapping[str, float]
    folds_evaluated: int
    out_of_sample: bool
    leakage_checks_passed: bool
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ReproducibilityRecord:
    random_seed: int
    code_version: str
    environment_fingerprint: str
    dependency_fingerprint: str
    training_command: str


@dataclass(frozen=True)
class GovernedModel:
    model_id: str
    version: str
    purpose: str
    dataset_fingerprint: str
    feature_set_fingerprint: str
    hyperparameters: Mapping[str, Any]
    reproducibility: ReproducibilityRecord
    stage: ModelStage = ModelStage.CHALLENGER
    artifact_uri: str | None = None
    parent_model_version: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromotionPolicy:
    policy_id: str
    version: str
    minimum_metrics: Mapping[str, float]
    maximum_metrics: Mapping[str, float]
    minimum_folds: int
    require_out_of_sample: bool
    require_leakage_checks: bool

    def __post_init__(self) -> None:
        if self.minimum_folds < 1:
            raise ValueError("minimum_folds must be >= 1")

    def evaluate(self, report: EvaluationReport) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if report.folds_evaluated < self.minimum_folds:
            reasons.append("insufficient_walk_forward_folds")
        if self.require_out_of_sample and not report.out_of_sample:
            reasons.append("out_of_sample_required")
        if self.require_leakage_checks and not report.leakage_checks_passed:
            reasons.append("leakage_checks_failed")
        combined = dict(report.metrics)
        combined.update({f"calibration.{k}": v for k, v in report.calibration_metrics.items()})
        for name, minimum in self.minimum_metrics.items():
            if name not in combined or combined[name] < minimum:
                reasons.append(f"minimum_metric_failed:{name}")
        for name, maximum in self.maximum_metrics.items():
            if name not in combined or combined[name] > maximum:
                reasons.append(f"maximum_metric_failed:{name}")
        return (not reasons, tuple(reasons))


@dataclass(frozen=True)
class DriftAssessment:
    model_id: str
    model_version: str
    feature_drift: Mapping[str, float]
    prediction_drift: Mapping[str, float]
    performance_drift: Mapping[str, float]
    threshold_breaches: Sequence[str]
    evaluated_at: datetime

    @property
    def drift_detected(self) -> bool:
        return bool(self.threshold_breaches)


@dataclass(frozen=True)
class RetrainingPolicy:
    policy_id: str
    version: str
    retrain_on_drift: bool
    maximum_model_age: timedelta | None

    def decide(self, *, drift: DriftAssessment, model_created_at: datetime, as_of: datetime) -> tuple[bool, str]:
        if as_of.tzinfo is None or model_created_at.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        if self.retrain_on_drift and drift.drift_detected:
            return True, "drift_threshold_breached"
        if self.maximum_model_age is not None and as_of - model_created_at >= self.maximum_model_age:
            return True, "maximum_model_age_reached"
        return False, "no_retraining_trigger"


@dataclass(frozen=True)
class ModelAuditEvent:
    action: str
    model_id: str
    model_version: str
    reason: str
    policy_version: str | None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InMemoryGovernedModelRegistry:
    """Reference registry with explicit promotion/rollback and immutable audit trail.

    Production storage can replace this adapter without changing governance rules.
    """

    def __init__(self) -> None:
        self._models: dict[tuple[str, str], GovernedModel] = {}
        self._champions: dict[str, tuple[str, str]] = {}
        self._audit: list[ModelAuditEvent] = []

    @property
    def audit_log(self) -> tuple[ModelAuditEvent, ...]:
        return tuple(self._audit)

    def register(self, model: GovernedModel) -> None:
        key = (model.model_id, model.version)
        if key in self._models:
            raise ValueError("model version already registered")
        self._models[key] = model
        self._audit.append(ModelAuditEvent("register", model.model_id, model.version, "registered_as_challenger", None))

    def get(self, model_id: str, version: str) -> GovernedModel | None:
        return self._models.get((model_id, version))

    def champion(self, purpose: str) -> GovernedModel | None:
        key = self._champions.get(purpose)
        return self._models.get(key) if key else None

    def promote(self, model_id: str, version: str, report: EvaluationReport, policy: PromotionPolicy) -> GovernedModel:
        key = (model_id, version)
        model = self._models.get(key)
        if model is None:
            raise KeyError("model not registered")
        if report.model_id != model_id or report.model_version != version:
            raise ValueError("evaluation report does not match model")
        if report.dataset_fingerprint != model.dataset_fingerprint:
            raise ValueError("evaluation dataset fingerprint does not match model lineage")
        approved, reasons = policy.evaluate(report)
        if not approved:
            self._audit.append(ModelAuditEvent("promotion_rejected", model_id, version, ",".join(reasons), policy.version))
            raise ValueError("promotion policy failed: " + ",".join(reasons))

        existing_key = self._champions.get(model.purpose)
        if existing_key and existing_key in self._models:
            existing = self._models[existing_key]
            self._models[existing_key] = replace(existing, stage=ModelStage.RETIRED)
            self._audit.append(ModelAuditEvent("retire", existing.model_id, existing.version, "replaced_by_new_champion", policy.version))

        promoted = replace(model, stage=ModelStage.CHAMPION)
        self._models[key] = promoted
        self._champions[model.purpose] = key
        self._audit.append(ModelAuditEvent("promote", model_id, version, "promotion_policy_passed", policy.version))
        return promoted

    def rollback(self, purpose: str, target_model_id: str, target_version: str, reason: str) -> GovernedModel:
        target_key = (target_model_id, target_version)
        target = self._models.get(target_key)
        if target is None:
            raise KeyError("rollback target not registered")
        if target.purpose != purpose:
            raise ValueError("rollback target purpose mismatch")

        current_key = self._champions.get(purpose)
        if current_key and current_key in self._models:
            current = self._models[current_key]
            self._models[current_key] = replace(current, stage=ModelStage.ROLLED_BACK)
            self._audit.append(ModelAuditEvent("rollback_from", current.model_id, current.version, reason, None))

        restored = replace(target, stage=ModelStage.CHAMPION)
        self._models[target_key] = restored
        self._champions[purpose] = target_key
        self._audit.append(ModelAuditEvent("rollback_to", target_model_id, target_version, reason, None))
        return restored
