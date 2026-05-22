from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from trading.models import ReliabilityThresholds


@dataclass(frozen=True)
class IbkrConfig:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str | None = None
    chat_id: str | None = None


@dataclass(frozen=True)
class MarketConfig:
    symbols: list[str] = field(default_factory=list)
    asset_type: str = "stock"
    exchange: str = "SMART"
    currency: str = "USD"


@dataclass(frozen=True)
class AlgorithmConfig:
    name: str = "sample_momentum"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunConfig:
    mode: str = "backtest"
    initial_cash: float = 10_000.0
    require_reliability: bool = True


@dataclass(frozen=True)
class RuntimeConfig:
    ibkr: IbkrConfig = field(default_factory=IbkrConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    market: MarketConfig = field(default_factory=MarketConfig)
    algorithm: AlgorithmConfig = field(default_factory=AlgorithmConfig)
    run: RunConfig = field(default_factory=RunConfig)
    reliability: ReliabilityThresholds = field(default_factory=ReliabilityThresholds)


def load_runtime_config(
    *,
    global_path: str | Path | None = None,
    algorithm_path: str | Path | None = None,
    run_path: str | Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> RuntimeConfig:
    raw: dict[str, Any] = {}
    for path in (global_path, algorithm_path, run_path):
        raw = _deep_merge(raw, _load_toml(path))
    raw = _deep_merge(raw, _env_overrides())
    raw = _deep_merge(raw, cli_overrides or {})
    return _to_runtime_config(raw)


def _load_toml(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    file_path = Path(path)
    if not file_path.exists():
        return {}
    with file_path.open("rb") as handle:
        return tomllib.load(handle)


def _env_overrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        overrides.setdefault("telegram", {})["bot_token"] = os.environ["TELEGRAM_BOT_TOKEN"]
    if os.getenv("TELEGRAM_CHAT_ID"):
        overrides.setdefault("telegram", {})["chat_id"] = os.environ["TELEGRAM_CHAT_ID"]
    if os.getenv("IBKR_HOST"):
        overrides.setdefault("ibkr", {})["host"] = os.environ["IBKR_HOST"]
    if os.getenv("IBKR_PORT"):
        overrides.setdefault("ibkr", {})["port"] = int(os.environ["IBKR_PORT"])
    if os.getenv("IBKR_CLIENT_ID"):
        overrides.setdefault("ibkr", {})["client_id"] = int(os.environ["IBKR_CLIENT_ID"])
    return overrides


def _to_runtime_config(raw: dict[str, Any]) -> RuntimeConfig:
    ibkr = raw.get("ibkr", {})
    telegram = raw.get("telegram", {})
    market = raw.get("market", {})
    algorithm = raw.get("algorithm", {})
    run = raw.get("run", {})
    reliability = raw.get("reliability", {})

    algorithm_name = str(algorithm.get("name", "sample_momentum"))
    algorithm_params = {key: value for key, value in algorithm.items() if key != "name"}

    return RuntimeConfig(
        ibkr=IbkrConfig(
            host=str(ibkr.get("host", "127.0.0.1")),
            port=int(ibkr.get("port", 7497)),
            client_id=int(ibkr.get("client_id", 1)),
        ),
        telegram=TelegramConfig(
            bot_token=telegram.get("bot_token"),
            chat_id=telegram.get("chat_id"),
        ),
        market=MarketConfig(
            symbols=[str(symbol) for symbol in market.get("symbols", [])],
            asset_type=str(market.get("asset_type", "stock")),
            exchange=str(market.get("exchange", "SMART")),
            currency=str(market.get("currency", "USD")),
        ),
        algorithm=AlgorithmConfig(name=algorithm_name, params=algorithm_params),
        run=RunConfig(
            mode=str(run.get("mode", "backtest")),
            initial_cash=float(run.get("initial_cash", 10_000.0)),
            require_reliability=bool(run.get("require_reliability", True)),
        ),
        reliability=ReliabilityThresholds(
            min_trades=int(reliability.get("min_trades", 1)),
            min_sharpe=float(reliability.get("min_sharpe", 0.0)),
            max_drawdown=float(reliability.get("max_drawdown", 0.20)),
            require_positive_return=bool(reliability.get("require_positive_return", True)),
        ),
    )


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
