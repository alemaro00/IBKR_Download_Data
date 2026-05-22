from __future__ import annotations

from collections.abc import Callable, Iterable

from trading.algorithms.base import TradingAlgorithm
from trading.models import AlgorithmDecision, BacktestResult, Candle, ReliabilityThresholds, Signal
from trading.runtime.reliability import evaluate_reliability
from trading.telegram import format_decision_message


class ReliabilityGateError(RuntimeError):
    """Raised when live alerts are blocked by backtest reliability settings."""


def run_live_alerts(
    *,
    algorithm: TradingAlgorithm,
    candles: Iterable[Candle],
    publish: Callable[[str], None],
    latest_backtest: BacktestResult | None = None,
    thresholds: ReliabilityThresholds | None = None,
    require_reliability: bool = True,
) -> list[AlgorithmDecision]:
    """Run the live alert path over incoming candles without placing orders."""
    if require_reliability:
        if latest_backtest is None or thresholds is None:
            raise ReliabilityGateError("Live alerts require a passing backtest reliability report.")
        report = evaluate_reliability(latest_backtest, thresholds)
        if not report.passed:
            raise ReliabilityGateError("; ".join(report.reasons))

    decisions: list[AlgorithmDecision] = []
    for candle in candles:
        decision = algorithm.on_candle(candle)
        decisions.append(decision)
        if decision.signal != Signal.HOLD:
            publish(format_decision_message(decision))
    return decisions

