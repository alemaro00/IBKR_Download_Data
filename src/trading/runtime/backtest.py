from __future__ import annotations

import math
from statistics import mean, pstdev

from trading.algorithms.base import TradingAlgorithm
from trading.models import BacktestResult, Candle, Signal


def run_backtest(
    algorithm: TradingAlgorithm,
    candles: list[Candle],
    initial_cash: float,
) -> BacktestResult:
    """Replay candles through an algorithm and compute simple long-only metrics."""
    if not candles:
        raise ValueError("Backtest requires at least one candle.")

    cash = float(initial_cash)
    position_units = 0.0
    entry_open = False
    trades = 0
    decisions = []
    equity_curve = [cash]
    returns = []

    previous_equity = cash
    for candle in candles:
        decision = algorithm.on_candle(candle)
        decisions.append(decision)

        if decision.signal == Signal.BUY and not entry_open and candle.close > 0:
            position_units = cash / candle.close
            cash = 0.0
            entry_open = True
            trades += 1
        elif decision.signal == Signal.SELL and entry_open:
            cash = position_units * candle.close
            position_units = 0.0
            entry_open = False

        equity = cash + position_units * candle.close
        equity_curve.append(equity)
        if previous_equity:
            returns.append((equity - previous_equity) / previous_equity)
        previous_equity = equity

    final_equity = equity_curve[-1]
    total_return = (final_equity - initial_cash) / initial_cash if initial_cash else 0.0
    max_drawdown = _max_drawdown(equity_curve)
    sharpe = _sharpe(returns)
    algorithm.finalize_run()

    return BacktestResult(
        algorithm_name=algorithm.name,
        initial_cash=float(initial_cash),
        final_equity=final_equity,
        total_return=total_return,
        max_drawdown=max_drawdown,
        sharpe=sharpe,
        trades=trades,
        decisions=decisions,
        equity_curve=equity_curve,
    )


def _max_drawdown(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak:
            worst = max(worst, (peak - value) / peak)
    return worst


def _sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    volatility = pstdev(returns)
    if volatility == 0:
        return 0.0
    return (mean(returns) / volatility) * math.sqrt(252)

