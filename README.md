# Python Project for Download Data from IBKR

Library: https://pypi.org/project/ib_async/

IBKR `whatToShow` reference: https://interactivebrokers.github.io/tws-api/historical_bars.html#hd_what_to_show

## IBKR setup check

This repo is configured for Trader Workstation paper trading by default:

- Host: `127.0.0.1`
- Port: `7497`
- Base client id: `1`

Before running historical, realtime, or portfolio-monitoring commands, log in to
TWS paper trading and verify that TWS is listening on the configured API socket:

```bash
uv run python scripts/check_ibkr_setup.py
```

If Codex sandboxing blocks local socket access or `uv` cache access, run the
already-created virtualenv directly:

```bash
PYTHONPATH=src .venv/bin/python scripts/check_ibkr_setup.py
```

The same preflight is also available through the main CLI:

```bash
uv run python main.py ibkr-check
```

Configuration is loaded from `config/global.toml` when present, then environment
variables override it:

- `IBKR_HOST` defaults to `127.0.0.1`
- `IBKR_PORT` defaults to `7497` for paper TWS
- `IBKR_CLIENT_ID` defaults to `1`

In TWS, enable API socket connections and make sure the socket port matches the
configured port before starting downloads.

## Historical data

Default streams are intentionally conservative:

- Forex: `BID`, `ASK`, `MIDPOINT`
- Stocks/futures: `TRADES`

Examples:

```bash
PYTHONPATH=src .venv/bin/python -m modules.historical_data forex EURUSD
PYTHONPATH=src .venv/bin/python -m modules.historical_data stock AAPL
PYTHONPATH=src .venv/bin/python -m modules.historical_data stock AAPL --streams TRADES
```

Use a unique client id when running more than one IBKR API process:

```bash
PYTHONPATH=src .venv/bin/python -m modules.historical_data forex EURUSD --client-id 11
PYTHONPATH=src .venv/bin/python -m modules.historical_data stock AAPL --streams TRADES --client-id 12
```

IBKR returns error `326` when two clients reuse the same client id. Stock
`BID`/`ASK`/`MIDPOINT` streams may require extra market-data subscriptions; AAPL
`TRADES` works in the tested paper TWS session.

## Smoke test

After TWS paper login, run the sequential smoke test:

```bash
scripts/smoke_ibkr.sh
```

It checks the socket, downloads `EURUSD` Forex historical bars, then downloads
`AAPL` stock `TRADES` bars with distinct client ids.
