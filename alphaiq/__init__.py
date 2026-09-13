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
from .pipeline import AlphaIQEngine
from .regime_intelligence import EnsemblePolicy, RegimeEnsembleClassifier, TransitionState
from .replay import DeterministicReplay, ReplayStep

__all__ = [
    "AlphaIQEngine",
    "DataQualityPolicy",
    "DataQualityReport",
    "DeterministicReplay",
    "EnsemblePolicy",
    "ExecutionReport",
    "FeatureCatalog",
    "FeatureSpec",
    "FeatureVector",
    "InMemorySnapshotStore",
    "JournalEvent",
    "MarketSnapshot",
    "OrderIntent",
    "PointInTimeFeatureEngine",
    "RegimeAssessment",
    "RegimeEnsembleClassifier",
    "RegimeLabel",
    "ReplayStep",
    "RiskDecision",
    "StrategyDecision",
    "TransitionState",
]

__version__ = "0.3.0"
