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
from .event_intelligence import (
    AbnormalityObservation,
    EventContext,
    EventContextBuilder,
    EventWindowPolicy,
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
from .strategy_portfolio import (
    ArbitrationPolicy,
    ConflictPolicy,
    PortfolioDecision,
    RankedStrategy,
    SignalSide,
    StrategyPortfolioEngine,
    StrategyPortfolioRegistration,
    StrategySignal,
)

__all__ = [
    "AbnormalityObservation",
    "AlphaIQEngine",
    "ArbitrationPolicy",
    "CalibrationArtifact",
    "ConflictPolicy",
    "DataQualityPolicy",
    "DataQualityReport",
    "DatasetManifest",
    "DeterministicReplay",
    "DriftAssessment",
    "EnsemblePolicy",
    "EvaluationReport",
    "EventContext",
    "EventContextBuilder",
    "EventWindowPolicy",
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
    "PortfolioDecision",
    "PromotionPolicy",
    "RankedStrategy",
    "RegimeAssessment",
    "RegimeEnsembleClassifier",
    "RegimeLabel",
    "ReplayStep",
    "ReproducibilityRecord",
    "RetrainingPolicy",
    "RiskDecision",
    "SignalSide",
    "StrategyDecision",
    "StrategyPortfolioEngine",
    "StrategyPortfolioRegistration",
    "StrategySignal",
    "TemporalFold",
    "TrainingRunManifest",
    "TransitionState",
    "WalkForwardPlan",
]

__version__ = "0.6.0"
