from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .domain import FeatureVector, MarketSnapshot, RegimeAssessment, RegimeLabel
from .contracts import RegimeClassifier


@dataclass(frozen=True)
class ModelMetadata:
    model_id: str
    version: str
    feature_set_version: str
    training_data_fingerprint: str
    training_window: str
    code_version: str
    approved: bool = False
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CalibrationReport:
    model_id: str
    model_version: str
    metric_name: str
    metric_value: float
    sample_size: int
    acceptable: bool


@dataclass(frozen=True)
class DriftReport:
    model_id: str
    model_version: str
    drift_detected: bool
    metrics: Mapping[str, float]
    reason: str


class ModelRegistry(Protocol):
    def champion(self, purpose: str) -> ModelMetadata | None: ...
    def get(self, model_id: str, version: str) -> ModelMetadata | None: ...


class Calibrator(Protocol):
    def validate(self, metadata: ModelMetadata) -> CalibrationReport: ...


class DriftMonitor(Protocol):
    def evaluate(self, metadata: ModelMetadata, features: FeatureVector) -> DriftReport: ...


class MLRegimeClassifier:
    """Production ML boundary.

    This class intentionally abstains until an approved model runtime is supplied.
    No unapproved model may silently influence trading decisions.
    """

    classifier_id = "ml-regime"

    def __init__(self, registry: ModelRegistry, version: str = "contract-v1") -> None:
        self.registry = registry
        self.version = version

    def classify(self, snapshot: MarketSnapshot, features: FeatureVector) -> RegimeAssessment:
        model = self.registry.champion("regime_classification")
        if model is None or not model.approved:
            return RegimeAssessment(
                label=RegimeLabel.UNKNOWN,
                confidence=None,
                probabilities={},
                evidence={"feature_set_version": features.feature_set_version},
                classifier_id=self.classifier_id,
                classifier_version=self.version,
                timestamp=snapshot.timestamp,
                provenance={"model": "none-approved"},
                abstained=True,
                reason="No approved champion regime model is available",
            )
        raise NotImplementedError("Approved model runtime adapter is TBD_SPEC")
