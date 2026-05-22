# Hourly FX Trading System Design

## Context

The system needs to support hourly FX strategies for instruments such as
`EURCHF` and `EURUSD`. It must acquire at least ten years of hourly data when a
provider can supply it, run repeatable backtests, process live hourly data, send
orders, and publish notifications and summaries to Telegram.

IBKR should not be treated as the guaranteed source for ten or more years of
history. The program must discover the earliest available IBKR data per
instrument, cache what it can retrieve, and keep the rest of the system
independent from that provider-specific retention limit.

## Goals

- Fetch hourly historical FX bars for configured instruments.
- Store normalized bars in local Parquet files.
- Validate and report NaN, infinite, duplicate, invalid, and missing bars.
- Run backtests from local Parquet data.
- Process live hourly candles for the same algorithm interface used by
  backtests.
- Send Telegram summaries for data quality, backtests, live decisions, and
  order events.
- Send orders through IBKR behind explicit safety gates.
- Keep the current homemade backtester until a library is justified by actual
  strategy complexity.

## Non-Goals

- Replacing the backtester immediately with `vectorbt`, `backtesting.py`, or
  `backtrader`.
- Building a broad market-data platform.
- Assuming IBKR can provide ten years of hourly data for every instrument.
- Silently repairing OHLC values by forward-filling tradable prices.

## Architecture

The system should be split into five small layers.

### Instruments

Instrument configuration should support FX symbols such as `EURCHF` and
`EURUSD` directly. The normalized `Instrument` model remains the boundary used
by algorithms, backtests, live data, and execution.

### Historical Providers

`IbkrHistoricalProvider` should:

- Ask IBKR for the earliest available data point before large downloads.
- Fetch hourly bars in paced chunks.
- Resume safely from the last cached timestamp.
- Return normalized candles and provider metadata.

The provider boundary should allow a future external data provider to supply
older history without changing algorithms or backtests.

### Parquet Store

Parquet is the canonical backtest source. Store one hourly dataset per
instrument under a predictable path such as:

```text
data/parquet/hourly/EURUSD.parquet
data/parquet/hourly/EURCHF.parquet
```

Each row should include:

- instrument symbol
- timestamp
- open
- high
- low
- close
- volume
- provider
- fetched_at

Backtests read from Parquet, not directly from IBKR.

### Data Quality

Add a validation layer that:

- Rejects NaN and infinite OHLC values.
- Rejects zero or negative OHLC values.
- Normalizes unavailable FX volume to null.
- Detects duplicate timestamps.
- Detects missing hourly bars.
- Produces a structured quality report.

Backtests should fail loudly on invalid OHLC data. Missing bars should be
reported before the run; whether they block a backtest should be configurable.
The default should block only severe gaps and invalid prices.

### Runtime

Backtest mode:

- Loads one or more instruments from Parquet.
- Runs the configured algorithm on normalized candles.
- Reports result metrics and data-quality summary.
- Publishes a Telegram summary when Telegram is configured.

Live mode:

- Builds hourly candles from IBKR live data or a reliable IBKR hourly update
  path.
- Uses the same `TradingAlgorithm.on_candle` interface as backtests.
- Publishes non-hold decisions and hourly summaries to Telegram.
- Does not place live orders unless execution is explicitly enabled.

Execution mode:

- Uses IBKR for order placement.
- Requires paper/live mode to be explicit.
- Applies a central request throttle.
- Emits Telegram order intent, accepted/rejected, filled, and error messages.

## Backtester Decision

Keep the homemade backtester for now. The current requirements are simple
enough to improve the existing implementation before adding a framework:

- hourly FX bars
- single-strategy decisions
- repeatable local data
- Telegram summaries
- controlled IBKR execution

Revisit a library when the system needs parameter sweeps, portfolio-level
accounting, advanced analyzers, commission/slippage modeling, or plotting.
`vectorbt` is the likely first candidate for parameter sweeps; `backtesting.py`
is simpler but less suitable for multi-instrument work; `backtrader` is
feature-rich but heavier.

## Error Handling

- Missing IBKR socket: fail before API work starts.
- IBKR retention shorter than requested: cache available data and report the
  shortfall.
- Pacing errors: retry with backoff and preserve partial cache.
- Invalid OHLC: fail the current ingestion/backtest.
- Missing hours: report count and ranges; block only when severity exceeds
  configured policy.
- Telegram unavailable: log and continue trading/backtesting logic.
- Order placement errors: publish error, stop execution for that decision, and
  keep the process alive when safe.

## Testing

Add focused tests for:

- FX instrument parsing for `EURCHF` and `EURUSD`.
- NaN, infinite, zero, and negative OHLC rejection.
- Duplicate timestamp detection.
- Missing hourly bar detection.
- Parquet round trip for normalized candles.
- Backtest loading from Parquet.
- IBKR historical provider chunk planning without live IBKR.
- Live hourly aggregation with synthetic ticks.
- Execution safety gates preventing accidental live orders.
- Telegram formatter output for quality, backtest, live, and order summaries.

## Implementation Order

1. Add FX instrument configuration and parsing.
2. Add data-quality validation for normalized candles.
3. Add Parquet read/write store.
4. Add cached historical download flow with IBKR earliest-data probing and
   paced chunking.
5. Make backtests read from Parquet.
6. Add live hourly aggregation.
7. Add execution layer with paper/live safety gates.
8. Add Telegram summaries and notifications across the new flow.

