from datetime import datetime, timedelta, timezone

from alphaiq.instrument_intelligence import EmpiricalMapPolicy, EmpiricalObservation, RankingWeights, build_empirical_map
from alphaiq.oos_intelligence import OOSIntelligencePolicy, build_oos_intelligence
from alphaiq.strategy_research import ImplementationState, StrategyResearchSpec
from alphaiq.validation import ResearchObservation


def obs(i, symbol, regime, result, fold="OOS", strategy="engine"):
    research = ResearchObservation(
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * i),
        symbol=symbol,
        timeframe="M15",
        regime=regime,
        strategy_id=strategy,
        strategy_version="1.0.0",
        outcome_r=result,
        feature_fingerprint="f1",
        configuration_version="c1",
        fold=fold,
    )
    return EmpiricalObservation(research, "H1", "M15", session="LONDON", mfe_r=max(result, 0) + 0.5, mae_r=max(-result, 0) + 0.2, slippage_r=0.01)


def implemented(strategy="engine"):
    return StrategyResearchSpec(strategy, "1.0.0", "test", frozenset({"STRONG_TREND", "RANGE"}), frozenset(), ImplementationState.IMPLEMENTED)


def weights():
    return RankingWeights(1.0, 0.1, 0.1, 0.05, 0.1, 0.1)


def test_report_uses_oos_only_and_excludes_train():
    rows = [obs(i, "XAUUSD", "STRONG_TREND", 0.5) for i in range(4)]
    rows += [obs(20 + i, "XAUUSD", "STRONG_TREND", 100.0, fold="train") for i in range(4)]
    matrix = build_empirical_map(rows, EmpiricalMapPolicy("m", minimum_sample_size=2))
    report = build_oos_intelligence(matrix, [implemented()], weights(), OOSIntelligencePolicy("p", minimum_total_samples=4, minimum_regime_samples=2))
    score = report.rankings_by_engine[("engine", "1.0.0")][0]
    assert score.sample_size == 4
    assert score.conservative_expectancy_r < 1.0


def test_manifest_only_strategy_is_never_ranked():
    rows = [obs(i, "XAUUSD", "STRONG_TREND", 1.0) for i in range(4)]
    matrix = build_empirical_map(rows, EmpiricalMapPolicy("m", minimum_sample_size=2))
    spec = StrategyResearchSpec("engine", "1.0.0", "test", frozenset({"STRONG_TREND"}), frozenset(), ImplementationState.MANIFEST_ONLY)
    report = build_oos_intelligence(matrix, [spec], weights(), OOSIntelligencePolicy("p", minimum_total_samples=4, minimum_regime_samples=2))
    assert report.rankings_by_engine == {}


def test_regime_mismatch_degradation_detects_wrong_regime_decay():
    rows = [obs(i, "USDJPY", "STRONG_TREND", 1.0) for i in range(4)]
    rows += [obs(20 + i, "USDJPY", "RANGE", -0.5) for i in range(4)]
    matrix = build_empirical_map(rows, EmpiricalMapPolicy("m", minimum_sample_size=2))
    report = build_oos_intelligence(matrix, [implemented()], weights(), OOSIntelligencePolicy("p", minimum_total_samples=8, minimum_regime_samples=4))
    score = report.rankings_by_engine[("engine", "1.0.0")][0]
    assert score.mismatch.eligible is True
    assert score.mismatch.preferred_regime == "STRONG_TREND"
    assert score.mismatch.degradation_r > 0
    assert score.mismatch.degradation_ratio > 0


def test_best_engine_by_instrument_is_exposed():
    rows = [obs(i, "XAUUSD", "STRONG_TREND", 0.2, strategy="a") for i in range(4)]
    rows += [obs(20 + i, "XAUUSD", "STRONG_TREND", 0.8, strategy="b") for i in range(4)]
    matrix = build_empirical_map(rows, EmpiricalMapPolicy("m", minimum_sample_size=2))
    report = build_oos_intelligence(matrix, [implemented("a"), implemented("b")], weights(), OOSIntelligencePolicy("p", minimum_total_samples=4, minimum_regime_samples=2))
    assert report.best_engine_by_instrument["XAUUSD"].strategy_id == "b"


def test_report_fingerprint_is_deterministic():
    rows = [obs(i, "XAUUSD", "STRONG_TREND", 0.5) for i in range(4)]
    matrix = build_empirical_map(rows, EmpiricalMapPolicy("m", minimum_sample_size=2))
    policy = OOSIntelligencePolicy("p", minimum_total_samples=4, minimum_regime_samples=2)
    a = build_oos_intelligence(matrix, [implemented()], weights(), policy)
    b = build_oos_intelligence(matrix, [implemented()], weights(), policy)
    assert a.fingerprint == b.fingerprint
