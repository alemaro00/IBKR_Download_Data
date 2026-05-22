from __future__ import annotations

from collections import defaultdict, deque

from trading.algorithms.base import TradingAlgorithm
from trading.models import AlgorithmDecision, Candle, Signal


class SampleMomentumAlgorithm(TradingAlgorithm):
    """Small reference algorithm used to prove the framework boundary."""

    name = "sample_momentum"
    required_history = 2

    def __init__(self) -> None:
        super().__init__()
        self.lookback = 2
        self.threshold = 0.01
        self._closes: dict[str, deque[float]] = defaultdict(deque)

    def configure(self, config: dict[str, object]) -> None:
        super().configure(config)
        self.lookback = max(1, int(config.get("lookback", self.lookback)))
        self.threshold = max(0.0, float(config.get("threshold", self.threshold)))
        self.required_history = self.lookback

    def on_candle(self, candle: Candle) -> AlgorithmDecision:
        history = self._closes[candle.instrument.symbol]
        history.append(float(candle.close))
        while len(history) > self.lookback:
            history.popleft()

        if len(history) < self.lookback:
            return AlgorithmDecision(
                algorithm_name=self.name,
                instrument=candle.instrument,
                timestamp=candle.timestamp,
                signal=Signal.HOLD,
                reason="waiting for history",
            )

        start = history[0]
        momentum = 0.0 if start == 0 else (history[-1] - start) / start
        if momentum > self.threshold:
            signal = Signal.BUY
        elif momentum < -self.threshold:
            signal = Signal.SELL
        else:
            signal = Signal.HOLD

        return AlgorithmDecision(
            algorithm_name=self.name,
            instrument=candle.instrument,
            timestamp=candle.timestamp,
            signal=signal,
            confidence=min(1.0, abs(momentum) / self.threshold) if self.threshold else 1.0,
            reason=f"{self.lookback}-bar momentum {momentum:.4f}",
            metadata={"momentum": momentum},
        )

