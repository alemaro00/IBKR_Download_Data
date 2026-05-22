from __future__ import annotations

import socket
from datetime import datetime
from typing import Any

from trading.config import IbkrConfig
from trading.models import Candle, Instrument


class IbkrConnectionError(RuntimeError):
    """Raised when TWS or IB Gateway is not reachable before API work starts."""


def preflight_ibkr_connection(config: IbkrConfig, *, timeout: float = 2.0) -> None:
    """Fail fast if the configured TWS/Gateway API socket is not reachable."""
    try:
        with socket.create_connection((config.host, config.port), timeout=timeout):
            return
    except OSError as exc:
        raise IbkrConnectionError(
            "IBKR API is not reachable at "
            f"{config.host}:{config.port}. Start TWS/IB Gateway, enable API connections, "
            "and confirm the configured port."
        ) from exc


def connect_ibkr(ib: Any, config: IbkrConfig, *, client_id_offset: int = 0, timeout: float = 4.0) -> None:
    """Connect an ib_async.IB instance after an explicit reachability check."""
    preflight_ibkr_connection(config)
    ib.connect(config.host, config.port, clientId=config.client_id + client_id_offset, timeout=timeout)


async def connect_ibkr_async(
    ib: Any,
    config: IbkrConfig,
    *,
    client_id_offset: int = 0,
    timeout: float = 4.0,
) -> None:
    """Connect an async ib_async.IB instance after an explicit reachability check."""
    preflight_ibkr_connection(config)
    await ib.connectAsync(config.host, config.port, clientId=config.client_id + client_id_offset, timeout=timeout)


def ibkr_bar_to_candle(bar: Any, instrument: Instrument) -> Candle:
    """Normalize an IBKR historical bar-like object into a framework candle."""
    timestamp = getattr(bar, "date")
    if not isinstance(timestamp, datetime):
        timestamp = datetime.fromisoformat(str(timestamp))

    volume = getattr(bar, "volume", None)
    return Candle(
        instrument=instrument,
        timestamp=timestamp,
        open=float(getattr(bar, "open")),
        high=float(getattr(bar, "high")),
        low=float(getattr(bar, "low")),
        close=float(getattr(bar, "close")),
        volume=float(volume) if volume is not None else None,
    )
