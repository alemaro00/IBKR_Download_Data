from __future__ import annotations

import os
import socket
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from trading.algorithms.sample_momentum import SampleMomentumAlgorithm
from trading.config import IbkrConfig
from trading.config import load_runtime_config
from trading.ibkr import IbkrConnectionError, ibkr_bar_to_candle, preflight_ibkr_connection
from trading.models import BacktestResult, Candle, Instrument, ReliabilityThresholds, Signal
from trading.runtime.backtest import run_backtest
from trading.runtime.live import ReliabilityGateError, run_live_alerts
from trading.runtime.reliability import evaluate_reliability
from trading.telegram import format_decision_message, format_daily_summary
from modules.historical_data import HistoricalDataUnavailable, print_historical_bars


class FakeIbkrBar:
    def __init__(self) -> None:
        self.date = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)
        self.open = 100.0
        self.high = 105.0
        self.low = 99.0
        self.close = 103.0
        self.volume = 1200


class TradingFrameworkTests(unittest.TestCase):
    def test_config_layers_files_env_and_cli_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            global_path = root / "global.toml"
            algorithm_path = root / "algorithm.toml"
            run_path = root / "run.toml"

            global_path.write_text(
                """
[ibkr]
host = "127.0.0.1"
port = 7497
client_id = 1

[algorithm]
name = "global_algo"
lookback = 3
threshold = 0.01

[reliability]
min_trades = 1
min_sharpe = 0.0
max_drawdown = 0.20
require_positive_return = true
""".strip(),
                encoding="utf-8",
            )
            algorithm_path.write_text(
                """
[algorithm]
name = "sample_momentum"
threshold = 0.02
""".strip(),
                encoding="utf-8",
            )
            run_path.write_text(
                """
[run]
mode = "backtest"
initial_cash = 25000

[market]
symbols = ["AAPL"]

[algorithm]
lookback = 5
""".strip(),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "TELEGRAM_BOT_TOKEN": "env-token",
                    "TELEGRAM_CHAT_ID": "env-chat",
                    "IBKR_CLIENT_ID": "42",
                },
                clear=False,
            ):
                cfg = load_runtime_config(
                    global_path=global_path,
                    algorithm_path=algorithm_path,
                    run_path=run_path,
                    cli_overrides={"run": {"initial_cash": 30000}},
                )

        self.assertEqual(cfg.algorithm.name, "sample_momentum")
        self.assertEqual(cfg.algorithm.params["lookback"], 5)
        self.assertEqual(cfg.algorithm.params["threshold"], 0.02)
        self.assertEqual(cfg.run.initial_cash, 30000)
        self.assertEqual(cfg.market.symbols, ["AAPL"])
        self.assertEqual(cfg.ibkr.client_id, 42)
        self.assertEqual(cfg.telegram.bot_token, "env-token")
        self.assertEqual(cfg.telegram.chat_id, "env-chat")

    def test_ibkr_bar_normalizes_to_candle_without_ibkr_dependency(self) -> None:
        instrument = Instrument(symbol="AAPL", asset_type="stock", exchange="SMART", currency="USD")
        candle = ibkr_bar_to_candle(FakeIbkrBar(), instrument)

        self.assertEqual(candle.instrument, instrument)
        self.assertEqual(candle.timestamp, datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc))
        self.assertEqual(candle.open, 100.0)
        self.assertEqual(candle.high, 105.0)
        self.assertEqual(candle.low, 99.0)
        self.assertEqual(candle.close, 103.0)
        self.assertEqual(candle.volume, 1200.0)

    def test_ibkr_preflight_fails_before_api_handshake_when_port_is_closed(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            closed_port = probe.getsockname()[1]

        with self.assertRaisesRegex(IbkrConnectionError, "127.0.0.1"):
            preflight_ibkr_connection(IbkrConfig(port=closed_port), timeout=0.1)

    def test_ibkr_preflight_accepts_open_socket(self) -> None:
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]

            preflight_ibkr_connection(IbkrConfig(port=port), timeout=0.1)

    def test_sample_momentum_emits_buy_hold_and_sell(self) -> None:
        instrument = Instrument(symbol="AAPL")
        algo = SampleMomentumAlgorithm()
        algo.configure({"lookback": 2, "threshold": 0.01})

        candles = [
            Candle(instrument, datetime(2026, 1, 1, tzinfo=timezone.utc), 100, 100, 100, 100),
            Candle(instrument, datetime(2026, 1, 2, tzinfo=timezone.utc), 100, 103, 99, 103),
            Candle(instrument, datetime(2026, 1, 3, tzinfo=timezone.utc), 103, 104, 102, 102),
            Candle(instrument, datetime(2026, 1, 4, tzinfo=timezone.utc), 102, 102, 95, 98),
        ]

        decisions = [algo.on_candle(candle) for candle in candles]

        self.assertEqual(decisions[0].signal, Signal.HOLD)
        self.assertEqual(decisions[1].signal, Signal.BUY)
        self.assertEqual(decisions[2].signal, Signal.HOLD)
        self.assertEqual(decisions[3].signal, Signal.SELL)

    def test_backtest_calculates_metrics_from_deterministic_candles(self) -> None:
        instrument = Instrument(symbol="AAPL")
        candles = [
            Candle(instrument, datetime(2026, 1, 1, tzinfo=timezone.utc), 100, 100, 100, 100),
            Candle(instrument, datetime(2026, 1, 2, tzinfo=timezone.utc), 100, 104, 100, 104),
            Candle(instrument, datetime(2026, 1, 3, tzinfo=timezone.utc), 104, 108, 104, 108),
            Candle(instrument, datetime(2026, 1, 4, tzinfo=timezone.utc), 108, 109, 105, 105),
            Candle(instrument, datetime(2026, 1, 5, tzinfo=timezone.utc), 105, 106, 104, 104),
        ]
        algorithm = SampleMomentumAlgorithm()
        algorithm.configure({"lookback": 2, "threshold": 0.01})

        result = run_backtest(algorithm, candles, initial_cash=10_000)

        self.assertGreaterEqual(result.trades, 1)
        self.assertGreater(result.final_equity, 10_000)
        self.assertGreater(result.total_return, 0.0)
        self.assertLessEqual(result.max_drawdown, 1.0)
        self.assertEqual(result.algorithm_name, "sample_momentum")

    def test_reliability_gate_reports_failures(self) -> None:
        result = BacktestResult(
            algorithm_name="sample",
            initial_cash=10_000,
            final_equity=9_500,
            total_return=-0.05,
            max_drawdown=0.30,
            sharpe=-0.5,
            trades=0,
            decisions=[],
            equity_curve=[],
        )
        thresholds = ReliabilityThresholds(
            min_trades=2,
            min_sharpe=0.0,
            max_drawdown=0.20,
            require_positive_return=True,
        )

        report = evaluate_reliability(result, thresholds)

        self.assertFalse(report.passed)
        self.assertIn("trades", " ".join(report.reasons))
        self.assertIn("positive", " ".join(report.reasons))

    def test_telegram_formatting_is_pure(self) -> None:
        instrument = Instrument(symbol="AAPL")
        decision = SampleMomentumAlgorithm().on_candle(
            Candle(instrument, datetime(2026, 1, 1, tzinfo=timezone.utc), 100, 100, 100, 100)
        )
        result = BacktestResult(
            algorithm_name="sample_momentum",
            initial_cash=10_000,
            final_equity=10_500,
            total_return=0.05,
            max_drawdown=0.02,
            sharpe=1.2,
            trades=3,
            decisions=[decision],
            equity_curve=[10_000, 10_500],
        )

        self.assertIn("sample_momentum", format_decision_message(decision))
        self.assertIn("Total return: 5.00%", format_daily_summary(result))

    def test_live_alerts_block_when_reliability_fails(self) -> None:
        instrument = Instrument(symbol="AAPL")
        candles = [
            Candle(instrument, datetime(2026, 1, 1, tzinfo=timezone.utc), 100, 100, 100, 100),
            Candle(instrument, datetime(2026, 1, 2, tzinfo=timezone.utc), 100, 101, 99, 101),
        ]
        result = BacktestResult(
            algorithm_name="sample_momentum",
            initial_cash=10_000,
            final_equity=9_000,
            total_return=-0.10,
            max_drawdown=0.10,
            sharpe=-1.0,
            trades=0,
            decisions=[],
            equity_curve=[10_000, 9_000],
        )

        with self.assertRaises(ReliabilityGateError):
            run_live_alerts(
                algorithm=SampleMomentumAlgorithm(),
                candles=candles,
                publish=lambda _message: None,
                latest_backtest=result,
                thresholds=ReliabilityThresholds(),
                require_reliability=True,
            )

    def test_legacy_market_modules_are_import_safe(self) -> None:
        __import__("modules.historical_data")
        __import__("modules.realtime_data")

    def test_historical_data_empty_bars_fail_loudly(self) -> None:
        with self.assertRaisesRegex(HistoricalDataUnavailable, "TRADES"):
            print_historical_bars("stock", {"TRADES": [], "BID": [object()], "ASK": [object()], "MIDPOINT": [object()]})

    def test_stock_historical_data_can_use_trades_when_quote_streams_are_missing(self) -> None:
        class FakeBar:
            date = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)
            open = 100.0
            high = 101.0
            low = 99.0
            close = 100.5
            volume = 10

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            print_historical_bars("stock", {"TRADES": [FakeBar()]})


if __name__ == "__main__":
    unittest.main()
