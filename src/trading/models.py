from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


@dataclass(frozen=True)
class Instrument:
    symbol: str
    asset_type: str = "stock"
    exchange: str = "SMART"
    currency: str = "USD"


@dataclass(frozen=True)
class Candle:
    instrument: Instrument
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    bid: float | None = None
    ask: float | None = None
    mid: float | None = None


class Signal(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class AlgorithmDecision:
    algorithm_name: str
    instrument: Instrument
    timestamp: datetime
    signal: Signal
    confidence: float = 0.0
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BacktestResult:
    algorithm_name: str
    initial_cash: float
    final_equity: float
    total_return: float
    max_drawdown: float
    sharpe: float
    trades: int
    decisions: list[AlgorithmDecision]
    equity_curve: list[float]


@dataclass(frozen=True)
class ReliabilityThresholds:
    min_trades: int = 1
    min_sharpe: float = 0.0
    max_drawdown: float = 0.20
    require_positive_return: bool = True


@dataclass(frozen=True)
class ReliabilityReport:
    passed: bool
    reasons: list[str]
    thresholds: ReliabilityThresholds

