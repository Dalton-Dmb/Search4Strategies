"""AlphaIQ Market Regime production package."""

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
from .pipeline import AlphaIQEngine

__all__ = [
    "AlphaIQEngine",
    "ExecutionReport",
    "FeatureVector",
    "JournalEvent",
    "MarketSnapshot",
    "OrderIntent",
    "RegimeAssessment",
    "RegimeLabel",
    "RiskDecision",
    "StrategyDecision",
]

__version__ = "0.1.0"
