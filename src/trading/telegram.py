from __future__ import annotations

from trading.models import AlgorithmDecision, BacktestResult


def format_decision_message(decision: AlgorithmDecision) -> str:
    return (
        f"[{decision.algorithm_name}] {decision.signal.value} "
        f"{decision.instrument.symbol} at {decision.timestamp.isoformat()}\n"
        f"Confidence: {decision.confidence:.2f}\n"
        f"Reason: {decision.reason}"
    )


def format_daily_summary(result: BacktestResult) -> str:
    return (
        f"Daily summary for {result.algorithm_name}\n"
        f"Initial equity: {result.initial_cash:.2f}\n"
        f"Final equity: {result.final_equity:.2f}\n"
        f"Total return: {result.total_return:.2%}\n"
        f"Max drawdown: {result.max_drawdown:.2%}\n"
        f"Sharpe: {result.sharpe:.2f}\n"
        f"Trades: {result.trades}"
    )

