from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import hashlib
import json
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PointInTimeLabelSpec:
    label_id: str
    version: str
    horizon: timedelta
    parameters: Mapping[str, Any]
    requires_future_outcome: bool

    def __post_init__(self) -> None:
        if self.horizon <= timedelta(0):
            raise ValueError("label horizon must be positive")
        if not self.version:
            raise ValueError("label version is required")

    def fingerprint(self) -> str:
        payload = {
            "label_id": self.label_id,
            "version": self.version,
            "horizon_seconds": self.horizon.total_seconds(),
            "parameters": dict(sorted(self.parameters.items())),
            "requires_future_outcome": self.requires_future_outcome,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class HyperparameterSearchManifest:
    search_id: str
    version: str
    algorithm: str
    objective_metric: str
    direction: str
    search_space: Mapping[str, Any]
    random_seed: int
    requested_trials: int

    def __post_init__(self) -> None:
        if self.direction not in {"maximize", "minimize"}:
            raise ValueError("direction must be maximize or minimize")
        if self.requested_trials < 1:
            raise ValueError("requested_trials must be >= 1")

    def fingerprint(self) -> str:
        payload = {
            "search_id": self.search_id,
            "version": self.version,
            "algorithm": self.algorithm,
            "objective_metric": self.objective_metric,
            "direction": self.direction,
            "search_space": self.search_space,
            "random_seed": self.random_seed,
            "requested_trials": self.requested_trials,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class HyperparameterTrial:
    trial_number: int
    parameters: Mapping[str, Any]
    objective_value: float
    fold_metrics: Sequence[Mapping[str, float]]
    completed: bool


@dataclass(frozen=True)
class CalibrationArtifact:
    calibration_id: str
    version: str
    method: str
    fit_dataset_fingerprint: str
    metrics_before: Mapping[str, float]
    metrics_after: Mapping[str, float]
    artifact_uri: str | None = None


@dataclass(frozen=True)
class TrainingRunManifest:
    run_id: str
    model_id: str
    model_version: str
    dataset_fingerprint: str
    label_fingerprint: str
    walk_forward_plan_version: str
    search_fingerprint: str | None
    selected_hyperparameters: Mapping[str, Any]
    calibration_id: str | None
    random_seed: int
    code_version: str
    dependency_fingerprint: str
    artifacts: Mapping[str, str] = field(default_factory=dict)
