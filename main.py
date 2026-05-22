from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from trading.algorithms.sample_momentum import SampleMomentumAlgorithm
from trading.config import RuntimeConfig, load_runtime_config
from trading.ibkr import IbkrConnectionError, preflight_ibkr_connection
from trading.models import Candle, Instrument
from trading.runtime.backtest import run_backtest
from trading.runtime.live import run_live_alerts
from trading.runtime.reliability import evaluate_reliability
from trading.telegram import format_daily_summary


def build_algorithm(config: RuntimeConfig) -> SampleMomentumAlgorithm:
    if config.algorithm.name != "sample_momentum":
        raise ValueError(f"Unsupported algorithm: {config.algorithm.name}")
    algorithm = SampleMomentumAlgorithm()
    algorithm.configure(config.algorithm.params)
    return algorithm


def demo_candles(config: RuntimeConfig) -> list[Candle]:
    symbol = config.market.symbols[0] if config.market.symbols else "AAPL"
    instrument = Instrument(
        symbol=symbol,
        asset_type=config.market.asset_type,
        exchange=config.market.exchange,
        currency=config.market.currency,
    )
    closes = [100.0, 104.0, 108.0, 105.0, 104.0, 110.0, 112.0, 109.0]
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles: list[Candle] = []
    previous = closes[0]
    for idx, close in enumerate(closes):
        open_price = previous
        candles.append(
            Candle(
                instrument=instrument,
                timestamp=start + timedelta(days=idx),
                open=open_price,
                high=max(open_price, close),
                low=min(open_price, close),
                close=close,
                volume=1000.0 + idx,
            )
        )
        previous = close
    return candles


def load_config_from_args(args: argparse.Namespace) -> RuntimeConfig:
    return load_runtime_config(
        global_path=args.global_config,
        algorithm_path=args.algorithm_config,
        run_path=args.run,
        cli_overrides={"run": {"initial_cash": args.initial_cash}} if args.initial_cash else None,
    )


def run_backtest_command(args: argparse.Namespace) -> int:
    config = load_config_from_args(args)
    result = run_backtest(build_algorithm(config), demo_candles(config), config.run.initial_cash)
    report = evaluate_reliability(result, config.reliability)

    print(format_daily_summary(result))
    print("Reliability: " + ("PASS" if report.passed else "FAIL"))
    for reason in report.reasons:
        print(f"- {reason}")
    return 0 if report.passed else 2


def run_live_alerts_command(args: argparse.Namespace) -> int:
    config = load_config_from_args(args)
    candles = demo_candles(config)
    latest_backtest = run_backtest(build_algorithm(config), candles, config.run.initial_cash)
    messages: list[str] = []
    decisions = run_live_alerts(
        algorithm=build_algorithm(config),
        candles=candles,
        publish=messages.append,
        latest_backtest=latest_backtest,
        thresholds=config.reliability,
        require_reliability=config.run.require_reliability,
    )

    for message in messages:
        print(message)
    print(f"Processed {len(decisions)} live candles. Orders were not placed.")
    return 0


def run_ibkr_check_command(args: argparse.Namespace) -> int:
    config = load_config_from_args(args)
    endpoint = f"{config.ibkr.host}:{config.ibkr.port}"
    print(f"Checking IBKR API endpoint {endpoint} with base client id {config.ibkr.client_id}...")
    try:
        sys.stdout.flush()
        preflight_ibkr_connection(config.ibkr)
    except IbkrConnectionError as exc:
        print(str(exc), file=sys.stderr)
        print(
            "Expected TWS/IB Gateway settings: API enabled, socket clients allowed, "
            f"and socket port {config.ibkr.port} matching this config.",
            file=sys.stderr,
        )
        return 2
    print("IBKR API socket is reachable. TWS/IB Gateway is ready for the next API handshake.")
    return 0


def run_portfolio_bot() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, "-m", "modules.portfolio_monitoring"], cwd=BASE_DIR, env=env)


def legacy_menu() -> None:
    print("Avvio dell'ecosistema IBKR...")
    print("Avvio del Bot Telegram (Portfolio Monitoring) in background...")

    bot_thread = threading.Thread(target=run_portfolio_bot, daemon=True)
    bot_thread.start()

    while True:
        print("\n" + "=" * 45)
        print("MENU PRINCIPALE - INTERACTIVE BROKERS")
        print("=" * 45)
        print("1. Scarica Dati Storici (historical_data.py)")
        print("2. Visualizza Dati Live (realtime_data.py)")
        print("3. Storico + Live (Flusso continuo)")
        print("4. Esci (Chiude anche il bot e l'ecosistema)")
        print("=" * 45)

        scelta = input("\nSeleziona un'opzione (1, 2, 3 o 4): ").strip()

        if scelta == "4":
            print("\nChiusura dell'intero ecosistema...")
            break

        if scelta in ["1", "2", "3"]:
            tipo = input("Vuoi operare su Forex o Stock/Futures? [forex/stock]: ").strip().lower()
            ticker = input("Inserisci il ticker (es: EURUSD o AAPL): ").strip().upper()

            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")

            if scelta == "1":
                subprocess.run([sys.executable, "-m", "modules.historical_data", tipo, ticker], cwd=BASE_DIR, env=env)
            elif scelta == "2":
                subprocess.run([sys.executable, "-m", "modules.realtime_data", tipo, ticker], cwd=BASE_DIR, env=env)
            elif scelta == "3":
                subprocess.run([sys.executable, "-m", "modules.historical_data", tipo, ticker], cwd=BASE_DIR, env=env)
                subprocess.run([sys.executable, "-m", "modules.realtime_data", tipo, ticker], cwd=BASE_DIR, env=env)
        else:
            print("\nScelta non valida. Riprova.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IBKR algorithm runtime")
    parser.add_argument("--global-config", default="config/global.toml")
    parser.add_argument("--algorithm-config", default="config/algorithms/sample_momentum.toml")
    parser.add_argument("--initial-cash", type=float)
    subparsers = parser.add_subparsers(dest="command")

    backtest = subparsers.add_parser("backtest", help="Run a deterministic backtest")
    backtest.add_argument("--run", required=True)
    backtest.set_defaults(func=run_backtest_command)

    live = subparsers.add_parser("live-alerts", help="Run live alert path without placing orders")
    live.add_argument("--run", required=True)
    live.set_defaults(func=run_live_alerts_command)

    ibkr_check = subparsers.add_parser("ibkr-check", help="Fail-fast check for TWS/IB Gateway API reachability")
    ibkr_check.add_argument("--run", default=None)
    ibkr_check.set_defaults(func=run_ibkr_check_command)

    legacy = subparsers.add_parser("legacy-menu", help="Open the original interactive menu")
    legacy.set_defaults(func=lambda _args: legacy_menu() or 0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
