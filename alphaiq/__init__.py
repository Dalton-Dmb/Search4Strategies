"""AlphaIQ Market Regime production package."""

from .data_platform import DataQualityPolicy, DataQualityReport, InMemorySnapshotStore
from .domain import (
    ExecutionReport,
    FeatureVector,
    JournalEvent,
    MarketSnapshot,
    OrderIntent,
    RegimeAssessment,
    RegimeLabel,
    RiskDecision,
    StrategyDecision,
)
from .feature_platform import FeatureCatalog, FeatureSpec, PointInTimeFeatureEngine
from .ml_governance import (
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
from .ml_training import (
    CalibrationArtifact,
    HyperparameterSearchManifest,
    HyperparameterTrial,
    PointInTimeLabelSpec,
    TrainingRunManifest,
)
from .pipeline import AlphaIQEngine
from .regime_intelligence import EnsemblePolicy, RegimeEnsembleClassifier, TransitionState
from .replay import DeterministicReplay, ReplayStep

__all__ = [
    "AlphaIQEngine",
    "CalibrationArtifact",
    "DataQualityPolicy",
    "DataQualityReport",
    "DatasetManifest",
    "DeterministicReplay",
    "DriftAssessment",
    "EnsemblePolicy",
    "EvaluationReport",
    "ExecutionReport",
    "FeatureCatalog",
    "FeatureSpec",
    "FeatureVector",
    "GovernedModel",
    "HyperparameterSearchManifest",
    "HyperparameterTrial",
    "InMemoryGovernedModelRegistry",
    "InMemorySnapshotStore",
    "JournalEvent",
    "MarketSnapshot",
    "ModelStage",
    "OrderIntent",
    "PointInTimeFeatureEngine",
    "PointInTimeLabelSpec",
    "PromotionPolicy",
    "RegimeAssessment",
    "RegimeEnsembleClassifier",
    "RegimeLabel",
    "ReplayStep",
    "ReproducibilityRecord",
    "RetrainingPolicy",
    "RiskDecision",
    "StrategyDecision",
    "TemporalFold",
    "TrainingRunManifest",
    "TransitionState",
    "WalkForwardPlan",
]

__version__ = "0.4.0"
