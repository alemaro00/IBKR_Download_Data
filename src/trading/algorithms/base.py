from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from trading.models import AlgorithmDecision, Candle


class TradingAlgorithm(ABC):
    """Base interface for backtest and live trading algorithms."""

    name: str
    required_history: int

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}

    def configure(self, config: dict[str, Any]) -> None:
        self._config = dict(config)

    @abstractmethod
    def on_candle(self, candle: Candle) -> AlgorithmDecision:
        """Return a decision for one normalized market candle."""
        raise NotImplementedError

    def finalize_run(self) -> None:
        """Optional hook for algorithms that need cleanup after a run."""

