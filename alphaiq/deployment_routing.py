"""Configuration-driven broker specialization and deployment routing for AlphaIQ™.

This module does not submit orders. It resolves canonical instruments to an
approved broker route and produces deterministic deployment lineage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping, Sequence

from .instrument_intelligence import InstrumentUniverse


class DeploymentMode(str, Enum):
    RESEARCH = "RESEARCH"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    LIVE = "LIVE"


@dataclass(frozen=True, slots=True)
class BrokerCapability:
    broker: str
    supported_symbols: frozenset[str]
    minimum_size: float
    price_precision: int
    supported_order_types: frozenset[str]
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.broker:
            raise ValueError("broker is required")
        if self.minimum_size <= 0:
            raise ValueError("minimum_size must be positive")
        if self.price_precision < 0:
            raise ValueError("price_precision cannot be negative")
        if not self.supported_order_types:
            raise ValueError("supported_order_types cannot be empty")


@dataclass(frozen=True, slots=True)
class InstrumentRoute:
    canonical_symbol: str
    broker: str
    broker_symbol: str
    priority: int = 0
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.canonical_symbol or not self.broker or not self.broker_symbol:
            raise ValueError("complete route identity is required")


@dataclass(frozen=True, slots=True)
class DeploymentPolicy:
    version: str
    mode: DeploymentMode
    live_release_approved: bool = False
    routes: tuple[InstrumentRoute, ...] = ()
    broker_capabilities: tuple[BrokerCapability, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("deployment policy version is required")
        if self.mode is DeploymentMode.LIVE and not self.live_release_approved:
            raise ValueError("LIVE mode requires explicit release approval")
        brokers = [item.broker for item in self.broker_capabilities]
        if len(brokers) != len(set(brokers)):
            raise ValueError("duplicate broker capabilities")


@dataclass(frozen=True, slots=True)
class ResolvedRoute:
    canonical_symbol: str
    broker: str
    broker_symbol: str
    deployment_mode: DeploymentMode


@dataclass(frozen=True, slots=True)
class DeploymentManifest:
    policy_version: str
    universe_version: str
    mode: DeploymentMode
    routes: tuple[InstrumentRoute, ...]
    code_version: str

    def fingerprint(self) -> str:
        payload = {
            "policy_version": self.policy_version,
            "universe_version": self.universe_version,
            "mode": self.mode.value,
            "routes": [
                {
                    "canonical_symbol": route.canonical_symbol,
                    "broker": route.broker,
                    "broker_symbol": route.broker_symbol,
                    "priority": route.priority,
                    "enabled": route.enabled,
                }
                for route in sorted(self.routes, key=lambda r: (r.canonical_symbol, -r.priority, r.broker, r.broker_symbol))
            ],
            "code_version": self.code_version,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def resolve_route(symbol: str, universe: InstrumentUniverse, policy: DeploymentPolicy) -> ResolvedRoute:
    universe.get(symbol)
    candidates = [route for route in policy.routes if route.enabled and route.canonical_symbol == symbol]
    if not candidates:
        raise KeyError(f"no enabled broker route for {symbol}")

    capabilities = {item.broker: item for item in policy.broker_capabilities if item.enabled}
    valid: list[InstrumentRoute] = []
    for route in candidates:
        capability = capabilities.get(route.broker)
        if capability is None:
            continue
        if route.broker_symbol not in capability.supported_symbols:
            continue
        valid.append(route)

    if not valid:
        raise ValueError(f"no broker capability supports configured route for {symbol}")

    selected = sorted(valid, key=lambda route: (-route.priority, route.broker, route.broker_symbol))[0]
    return ResolvedRoute(symbol, selected.broker, selected.broker_symbol, policy.mode)


def build_deployment_manifest(policy: DeploymentPolicy, universe: InstrumentUniverse, code_version: str) -> DeploymentManifest:
    if not code_version:
        raise ValueError("code_version is required")
    for route in policy.routes:
        universe.get(route.canonical_symbol)
    return DeploymentManifest(policy.version, universe.version, policy.mode, policy.routes, code_version)
