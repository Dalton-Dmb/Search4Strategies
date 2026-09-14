import pytest

from alphaiq.deployment_routing import (
    BrokerCapability,
    DeploymentMode,
    DeploymentPolicy,
    InstrumentRoute,
    build_deployment_manifest,
    resolve_route,
)
from alphaiq.instrument_intelligence import InstrumentSpec, InstrumentUniverse


def universe():
    return InstrumentUniverse(
        "u1",
        (
            InstrumentSpec("XAUUSD", "METAL", 100),
            InstrumentSpec("USDJPY", "FX", 90),
            InstrumentSpec("EURCHF", "FX", 80),
        ),
    )


def policy(mode=DeploymentMode.SHADOW, approved=False):
    return DeploymentPolicy(
        "d1",
        mode,
        approved,
        routes=(
            InstrumentRoute("XAUUSD", "pepperstone", "XAUUSD", 100),
            InstrumentRoute("USDJPY", "deriv", "USDJPY", 90),
            InstrumentRoute("EURCHF", "oanda", "EUR_CHF", 80),
        ),
        broker_capabilities=(
            BrokerCapability("pepperstone", frozenset({"XAUUSD"}), 0.01, 2, frozenset({"market", "limit"})),
            BrokerCapability("deriv", frozenset({"USDJPY"}), 0.01, 3, frozenset({"market"})),
            BrokerCapability("oanda", frozenset({"EUR_CHF"}), 1.0, 5, frozenset({"market", "limit"})),
        ),
    )


def test_specialized_routes_are_deterministic():
    p = policy()
    assert resolve_route("XAUUSD", universe(), p).broker == "pepperstone"
    assert resolve_route("USDJPY", universe(), p).broker == "deriv"
    assert resolve_route("EURCHF", universe(), p).broker_symbol == "EUR_CHF"


def test_live_mode_is_disabled_without_release_approval():
    with pytest.raises(ValueError):
        policy(DeploymentMode.LIVE, approved=False)
    assert policy(DeploymentMode.LIVE, approved=True).mode is DeploymentMode.LIVE


def test_route_requires_matching_enabled_broker_capability():
    bad = DeploymentPolicy(
        "d2",
        DeploymentMode.PAPER,
        routes=(InstrumentRoute("XAUUSD", "pepperstone", "GOLD", 1),),
        broker_capabilities=(BrokerCapability("pepperstone", frozenset({"XAUUSD"}), 0.01, 2, frozenset({"market"})),),
    )
    with pytest.raises(ValueError):
        resolve_route("XAUUSD", universe(), bad)


def test_deployment_manifest_fingerprint_is_reproducible():
    a = build_deployment_manifest(policy(), universe(), "code-1")
    b = build_deployment_manifest(policy(), universe(), "code-1")
    c = build_deployment_manifest(policy(), universe(), "code-2")
    assert a.fingerprint() == b.fingerprint()
    assert a.fingerprint() != c.fingerprint()
