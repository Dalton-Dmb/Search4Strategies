from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Mapping, Sequence

from .data_platform import DataQualityPolicy, validate_point_in_time
from .domain import FeatureVector, MarketSnapshot

FeatureFunction = Callable[[Sequence[MarketSnapshot], datetime], float | int | bool | None]


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    version: str
    family: str
    required_history: int
    function: FeatureFunction
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("feature name is required")
        if not self.version.strip():
            raise ValueError("feature version is required")
        if self.required_history < 1:
            raise ValueError("required_history must be >= 1")


@dataclass
class FeatureCatalog:
    _specs: dict[str, FeatureSpec] = field(default_factory=dict)

    def register(self, spec: FeatureSpec) -> None:
        existing = self._specs.get(spec.name)
        if existing is not None and existing.version != spec.version:
            raise ValueError(f"feature {spec.name!r} already registered with version {existing.version}")
        self._specs[spec.name] = spec

    def get(self, name: str) -> FeatureSpec:
        return self._specs[name]

    def specs(self) -> tuple[FeatureSpec, ...]:
        return tuple(self._specs[name] for name in sorted(self._specs))

    def fingerprint(self) -> str:
        manifest = [
            {
                "name": spec.name,
                "version": spec.version,
                "family": spec.family,
                "required_history": spec.required_history,
            }
            for spec in self.specs()
        ]
        encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class FeatureBuildResult:
    vector: FeatureVector | None
    valid: bool
    reasons: tuple[str, ...] = ()
    catalog_fingerprint: str | None = None


class PointInTimeFeatureEngine:
    def __init__(self, catalog: FeatureCatalog, quality_policy: DataQualityPolicy) -> None:
        self.catalog = catalog
        self.quality_policy = quality_policy

    def build(self, snapshots: Sequence[MarketSnapshot], *, as_of: datetime) -> FeatureBuildResult:
        quality = validate_point_in_time(snapshots, as_of=as_of, policy=self.quality_policy)
        if not quality.valid:
            return FeatureBuildResult(vector=None, valid=False, reasons=quality.reasons)

        eligible = tuple(item for item in snapshots if item.timestamp <= as_of)
        values: dict[str, float | int | bool | None] = {}
        provenance: dict[str, str] = {}
        reasons: list[str] = []

        for spec in self.catalog.specs():
            if len(eligible) < spec.required_history:
                reasons.append(f"insufficient_history:{spec.name}")
                continue
            value = spec.function(eligible, as_of)
            values[spec.name] = value
            provenance[spec.name] = f"{spec.family}:{spec.name}:{spec.version}"

        if reasons:
            return FeatureBuildResult(vector=None, valid=False, reasons=tuple(reasons))

        fingerprint = self.catalog.fingerprint()
        vector = FeatureVector(
            timestamp=as_of,
            values=values,
            feature_set_version=fingerprint,
            provenance=provenance,
        )
        return FeatureBuildResult(vector=vector, valid=True, catalog_fingerprint=fingerprint)


def candle_range(history: Sequence[MarketSnapshot], as_of: datetime) -> float:
    bar = history[-1]
    if bar.timestamp > as_of:
        raise ValueError("feature attempted to consume future data")
    return bar.high - bar.low


def candle_body(history: Sequence[MarketSnapshot], as_of: datetime) -> float:
    bar = history[-1]
    if bar.timestamp > as_of:
        raise ValueError("feature attempted to consume future data")
    return abs(bar.close - bar.open)


def close_return_1(history: Sequence[MarketSnapshot], as_of: datetime) -> float | None:
    current = history[-1]
    previous = history[-2]
    if current.timestamp > as_of:
        raise ValueError("feature attempted to consume future data")
    if previous.close == 0:
        return None
    return current.close / previous.close - 1.0
