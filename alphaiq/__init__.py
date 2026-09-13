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
from .replay import DeterministicReplay, ReplayStep

__all__ = [
    "AlphaIQEngine",
    "DataQualityPolicy",
    "DataQualityReport",
    "DeterministicReplay",
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
    "RegimeLabel",
    "ReplayStep",
    "RiskDecision",
    "StrategyDecision",
]

__version__ = "0.2.0"
