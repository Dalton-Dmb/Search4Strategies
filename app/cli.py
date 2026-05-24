from __future__ import annotations

import argparse
import json
import logging

import pandas as pd

from app.config.settings import get_settings, load_yaml
from app.data.mt5_client import MT5Client
from app.data.storage import save_candles, load_candles
from app.discovery.rule_miner import mine_boolean_rules
from app.execution.paper_replay import replay_recent_signals, summarize_replay
from app.execution.signal_engine import generate_signal
from app.execution.signal_scanner import scan_recent_signals
from app.features.candles import add_candle_features
from app.features.displacement import add_displacement_features
from app.features.fib import add_fib_features
from app.features.ichimoku import add_ichimoku_features
from app.features.mtf import merge_mtf_bias
from app.features.rsi_divergence import add_rsi_divergence_features
from app.features.structure import add_structure_features
from app.labelling.triple_barrier import label_trades
from app.models.train import train_classifier
from app.reports.portfolio_ranker import rank_portfolio_reports
from app.reports.reporting import write_discovery_report
from app.strategy.exporter import export_strategy
from app.utils.logging import configure_logging
from app.validation.monte_carlo import (
    extract_rule_outcomes,
    monte_carlo_simulation,
    risk_adjusted_monte_carlo,
    summarize_monte_carlo,
    summarize_risk_adjusted,
)
from app.validation.rule_validator import walk_forward_rule_validation
from app.validation.walk_forward import summarize_labels

log = logging.getLogger(__name__)


def build_features(df: pd.DataFrame, h4_df: pd.DataFrame | None = None, d1_df: pd.DataFrame | None = None) -> pd.DataFrame:
    feat = add_candle_features(df)
    feat = add_structure_features(feat)
    feat = add_fib_features(feat)
    feat = add_ichimoku_features(feat)
    feat = add_rsi_divergence_features(feat)
    feat = add_displacement_features(feat)

    if h4_df is not None or d1_df is not None:
        feat = merge_mtf_bias(feat, h4_df=h4_df, d1_df=d1_df)

    return feat


def build_labels(feat: pd.DataFrame, side: str, target_r: float, horizon: int) -> pd.DataFrame:
    if side == "long":
        return label_trades(feat, side=1, target_r=target_r, horizon=horizon)

    if side == "short":
        return label_trades(feat, side=-1, target_r=target_r, horizon=horizon)

    labels_long = label_trades(feat, side=1, target_r=target_r, horizon=horizon)
    labels_short = label_trades(feat, side=-1, target_r=target_r, horizon=horizon)

    return pd.concat([labels_long, labels_short], ignore_index=True)


def load_optional_htf(data_dir, symbol: str, use_h4: bool = False, use_d1: bool = False):
    h4_df = None
    d1_df = None

    if use_h4:
        try:
            h4_df = load_candles(data_dir, symbol, "H4")
        except Exception as exc:
            log.warning("Could not load H4 data for %s: %s", symbol, exc)

    if use_d1:
        try:
            d1_df = load_candles(data_dir, symbol, "D1")
        except Exception as exc:
            log.warning("Could not load D1 data for %s: %s", symbol, exc)

    return h4_df, d1_df


def cmd_doctor(args):
    s = get_settings()
    print(json.dumps({
        "root": str(s.root),
        "data_dir": str(s.data_dir),
        "reports_dir": str(s.reports_dir),
        "mt5_path_set": bool(s.mt5_path),
        "mt5_login_set": bool(s.mt5_login),
    }, indent=2))


def cmd_collect(args):
    s = get_settings()
    client = MT5Client(s.mt5_path, s.mt5_login, s.mt5_password, s.mt5_server)
    client.connect()

    try:
        df = client.fetch_rates(args.symbol, args.timeframe, args.bars)
        path = save_candles(df, s.data_dir)
        print(f"Saved {len(df)} candles to {path}")
    finally:
        client.shutdown()


def cmd_discover(args):
    s = get_settings()
    load_yaml()

    df = load_candles(s.data_dir, args.symbol, args.timeframe)

    h4_df, d1_df = load_optional_htf(
        s.data_dir,
        args.symbol,
        use_h4=args.use_htf,
        use_d1=args.use_htf,
    )

    feat = build_features(df, h4_df=h4_df, d1_df=d1_df)

    labels = build_labels(
        feat,
        side=args.side,
        target_r=args.target_r,
        horizon=args.horizon,
    )

    rules = mine_boolean_rules(
        feat,
        labels,
        min_samples=args.min_samples,
    )

    summary = summarize_labels(labels)

    importances = None

    try:
        trained = train_classifier(feat, labels)
        summary["model_report"] = trained["report"]
        importances = trained["importances"]
    except Exception as exc:
        summary["model_warning"] = str(exc)

    strategy_name = f"{args.symbol}_{args.timeframe}_{args.target_r}R"

    report_dir = write_discovery_report(
        s.reports_dir,
        strategy_name,
        rules,
        summary,
        importances,
    )

    export_path = export_strategy(
        s.root / "storage" / "strategies" / f"{strategy_name}.json",
        rules,
        {
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "target_r": args.target_r,
            "horizon": args.horizon,
            "side": args.side,
            "use_htf": args.use_htf,
        },
    )

    print(f"Report written to {report_dir}")
    print(f"Strategy exported to {export_path}")

    if not rules.empty:
        print(rules.head(20).to_string(index=False))
    else:
        print("No robust rules found. Increase data or reduce min_samples.")


def cmd_validate(args):
    s = get_settings()

    strategy_path = (
        s.root
        / "storage"
        / "strategies"
        / f"{args.symbol}_{args.timeframe}_{args.target_r}R.json"
    )

    if not strategy_path.exists():
        raise FileNotFoundError(f"Strategy file not found: {strategy_path}")

    strategy = json.loads(strategy_path.read_text(encoding="utf-8"))

    if args.rule:
        rule = args.rule
    else:
        approved = strategy.get("approved_rules", [])
        if not approved:
            raise ValueError("No approved rules found in strategy JSON.")
        rule = approved[0]["rule"]

    df = load_candles(s.data_dir, args.symbol, args.timeframe)
    feat = build_features(df)

    labels = build_labels(
        feat,
        side=args.side,
        target_r=args.target_r,
        horizon=args.horizon,
    )

    wf = walk_forward_rule_validation(
        feat,
        labels,
        rule=rule,
        folds=args.folds,
        min_samples=args.min_samples,
    )

    output_dir = s.reports_dir / f"{args.symbol}_{args.timeframe}_{args.target_r}R"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "walk_forward_validation.csv"
    wf.to_csv(output_path, index=False)

    print(f"Validated rule: {rule}")
    print(f"Walk-forward report written to {output_path}")
    print()
    print(wf.to_string(index=False))

    valid = wf[wf["samples"] > 0]

    if not valid.empty:
        print()
        print("Aggregate validation:")
        print(f"Average win rate: {valid['win_rate'].mean():.4f}")
        print(f"Average expectancy R: {valid['expectancy_r'].mean():.4f}")
        print(f"Average profit factor: {valid['profit_factor'].mean():.4f}")
        print(f"Positive folds: {(valid['expectancy_r'] > 0).sum()} / {len(valid)}")
    else:
        print("No valid fold samples found.")


def cmd_montecarlo(args):
    s = get_settings()

    strategy_path = (
        s.root
        / "storage"
        / "strategies"
        / f"{args.symbol}_{args.timeframe}_{args.target_r}R.json"
    )

    if not strategy_path.exists():
        raise FileNotFoundError(f"Strategy file not found: {strategy_path}")

    strategy = json.loads(strategy_path.read_text(encoding="utf-8"))

    if args.rule:
        rule = args.rule
    else:
        approved = strategy.get("approved_rules", [])
        if not approved:
            raise ValueError("No approved rules found in strategy JSON.")
        rule = approved[0]["rule"]

    df = load_candles(s.data_dir, args.symbol, args.timeframe)
    feat = build_features(df)

    labels = build_labels(
        feat,
        side=args.side,
        target_r=args.target_r,
        horizon=args.horizon,
    )

    outcomes = extract_rule_outcomes(
        feat,
        labels,
        rule=rule,
        target_r=args.target_r,
    )

    if not outcomes:
        print("No outcomes generated for Monte Carlo.")
        return

    output_dir = s.reports_dir / f"{args.symbol}_{args.timeframe}_{args.target_r}R"
    output_dir.mkdir(parents=True, exist_ok=True)

    mc = monte_carlo_simulation(
        outcomes,
        runs=args.runs,
    )

    mc_path = output_dir / "monte_carlo_r_units.csv"
    mc.to_csv(mc_path, index=False)

    mc_summary = summarize_monte_carlo(mc)

    risk_mc = risk_adjusted_monte_carlo(
        outcomes,
        runs=args.runs,
        starting_balance=args.balance,
        risk_per_trade=args.risk,
    )

    risk_path = output_dir / "monte_carlo_risk_adjusted.csv"
    risk_mc.to_csv(risk_path, index=False)

    risk_summary = summarize_risk_adjusted(risk_mc)

    print(f"Monte Carlo rule: {rule}")
    print(f"R-unit report written to {mc_path}")
    print(f"Risk-adjusted report written to {risk_path}")
    print()

    print("R-unit summary:")
    for k, v in mc_summary.items():
        print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")

    print()
    print("Risk-adjusted summary:")
    for k, v in risk_summary.items():
        print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")


def cmd_signal(args):
    s = get_settings()

    df = load_candles(s.data_dir, args.symbol, args.timeframe)
    feat = build_features(df)

    signal = generate_signal(
        features=feat,
        symbol=args.symbol,
        timeframe=args.timeframe,
        rule=args.rule,
        side=args.side,
        target_r=args.target_r,
    )

    if signal is None:
        print("No signal generated.")
        return

    print()
    print("SIGNAL ENGINE OUTPUT")
    print("-" * 50)

    for field, value in signal.__dict__.items():
        print(f"{field}: {value}")


def cmd_scan(args):
    s = get_settings()

    df = load_candles(s.data_dir, args.symbol, args.timeframe)
    feat = build_features(df)

    signals = scan_recent_signals(
        features=feat,
        symbol=args.symbol,
        timeframe=args.timeframe,
        rule=args.rule,
        side=args.side,
        target_r=args.target_r,
        lookback=args.lookback,
    )

    if signals.empty:
        print("No valid signals found in lookback window.")
        return

    output_dir = s.reports_dir / f"{args.symbol}_{args.timeframe}_{args.target_r}R"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "recent_signals.csv"
    signals.to_csv(output_path, index=False)

    print(f"Signals found: {len(signals)}")
    print(f"Signal scan written to {output_path}")
    print()
    print(signals.tail(20).to_string(index=False))


def replay_filename(args) -> str:
    suffix = []

    if args.require_h4_bull:
        suffix.append("h4_bull")

    if args.require_d1_bull:
        suffix.append("d1_bull")

    if args.require_rsi_bull:
        suffix.append("rsi_bull")

    name = "paper_replay"

    if suffix:
        name += "_" + "_".join(suffix)

    return f"{name}.csv"


def cmd_replay(args):
    s = get_settings()

    candles = load_candles(s.data_dir, args.symbol, args.timeframe)

    h4_df, d1_df = load_optional_htf(
        s.data_dir,
        args.symbol,
        use_h4=args.require_h4_bull,
        use_d1=args.require_d1_bull,
    )

    feat = build_features(
        candles,
        h4_df=h4_df,
        d1_df=d1_df,
    )

    results = replay_recent_signals(
        candles=candles,
        features=feat,
        symbol=args.symbol,
        timeframe=args.timeframe,
        rule=args.rule,
        side=args.side,
        target_r=args.target_r,
        lookback=args.lookback,
        horizon=args.horizon,
        require_h4_bull=args.require_h4_bull,
        require_d1_bull=args.require_d1_bull,
        require_rsi_bull=args.require_rsi_bull,
    )

    if results.empty:
        print("No replayable signals found.")
        return

    output_dir = s.reports_dir / f"{args.symbol}_{args.timeframe}_{args.target_r}R"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / replay_filename(args)
    results.to_csv(output_path, index=False)

    summary = summarize_replay(results)

    print(f"Paper replay written to {output_path}")
    print()

    print("Replay summary:")
    for k, v in summary.items():
        print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")

    print()
    print(results.tail(20).to_string(index=False))


def cmd_portfolio(args):
    s = get_settings()

    ranked = rank_portfolio_reports(s.reports_dir)

    if ranked.empty:
        print("No paper replay reports found.")
        return

    output_path = s.reports_dir / "portfolio_ranking.csv"
    ranked.to_csv(output_path, index=False)

    print(f"Portfolio ranking written to {output_path}")
    print()
    print(ranked.head(args.top).to_string(index=False))


def main():
    settings = get_settings()
    configure_logging(settings.root)

    parser = argparse.ArgumentParser("Search4Strategies")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("doctor")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("collect")
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="M30")
    p.add_argument("--bars", type=int, default=10000)
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("discover")
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="M30")
    p.add_argument("--target-r", type=float, default=3.0)
    p.add_argument("--horizon", type=int, default=48)
    p.add_argument("--side", choices=["long", "short", "both"], default="both")
    p.add_argument("--min-samples", type=int, default=40)
    p.add_argument("--use-htf", action="store_true")
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("validate")
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="M30")
    p.add_argument("--target-r", type=float, default=3.0)
    p.add_argument("--horizon", type=int, default=72)
    p.add_argument("--side", choices=["long", "short", "both"], default="short")
    p.add_argument("--folds", type=int, default=5)
    p.add_argument("--min-samples", type=int, default=1)
    p.add_argument("--rule", default=None)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("montecarlo")
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="M30")
    p.add_argument("--target-r", type=float, default=3.0)
    p.add_argument("--horizon", type=int, default=72)
    p.add_argument("--side", choices=["long", "short", "both"], default="short")
    p.add_argument("--runs", type=int, default=1000)
    p.add_argument("--rule", default=None)
    p.add_argument("--balance", type=float, default=10000.0)
    p.add_argument("--risk", type=float, default=0.005)
    p.set_defaults(func=cmd_montecarlo)

    p = sub.add_parser("signal")
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="M30")
    p.add_argument("--target-r", type=float, default=5.0)
    p.add_argument("--side", choices=["long", "short"], required=True)
    p.add_argument("--rule", required=True)
    p.set_defaults(func=cmd_signal)

    p = sub.add_parser("scan")
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="M30")
    p.add_argument("--target-r", type=float, default=5.0)
    p.add_argument("--side", choices=["long", "short"], required=True)
    p.add_argument("--rule", required=True)
    p.add_argument("--lookback", type=int, default=300)
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("replay")
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="M30")
    p.add_argument("--target-r", type=float, default=5.0)
    p.add_argument("--horizon", type=int, default=120)
    p.add_argument("--side", choices=["long", "short"], required=True)
    p.add_argument("--rule", required=True)
    p.add_argument("--lookback", type=int, default=1000)
    p.add_argument("--require-h4-bull", action="store_true")
    p.add_argument("--require-d1-bull", action="store_true")
    p.add_argument("--require-rsi-bull", action="store_true")
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser("portfolio")
    p.add_argument("--top", type=int, default=20)
    p.set_defaults(func=cmd_portfolio)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
