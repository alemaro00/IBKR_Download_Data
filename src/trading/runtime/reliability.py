from __future__ import annotations

from trading.models import BacktestResult, ReliabilityReport, ReliabilityThresholds


def evaluate_reliability(
    result: BacktestResult,
    thresholds: ReliabilityThresholds,
) -> ReliabilityReport:
    reasons: list[str] = []
    if result.trades < thresholds.min_trades:
        reasons.append(f"trades {result.trades} below minimum {thresholds.min_trades}")
    if result.sharpe < thresholds.min_sharpe:
        reasons.append(f"sharpe {result.sharpe:.2f} below minimum {thresholds.min_sharpe:.2f}")
    if result.max_drawdown > thresholds.max_drawdown:
        reasons.append(
            f"max drawdown {result.max_drawdown:.2%} above limit {thresholds.max_drawdown:.2%}"
        )
    if thresholds.require_positive_return and result.total_return <= 0:
        reasons.append("positive return required")

    return ReliabilityReport(
        passed=not reasons,
        reasons=reasons,
        thresholds=thresholds,
    )

