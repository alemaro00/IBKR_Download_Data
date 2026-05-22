from __future__ import annotations

import argparse
import sys

from trading.config import load_runtime_config
from trading.ibkr import connect_ibkr


class HistoricalDataUnavailable(RuntimeError):
    """Raised when IBKR returns no historical bars for one or more requested streams."""


DEFAULT_STREAMS_BY_TYPE = {
    "forex": ["BID", "ASK", "MIDPOINT"],
    "stock": ["TRADES"],
}
VALID_STREAMS = {"TRADES", "BID", "ASK", "MIDPOINT"}


def default_streams(tipo: str) -> list[str]:
    return list(DEFAULT_STREAMS_BY_TYPE["forex" if tipo == "forex" else "stock"])


def build_contract(ib_module, tipo: str, ticker: str):
    if tipo == "forex":
        return ib_module.Forex(ticker)
    return ib_module.Stock(ticker, "SMART", "USD")


def fetch_historical_bars(ib, contract, streams: list[str]):
    common = {
        "endDateTime": "",
        "durationStr": "1 D",
        "barSizeSetting": "1 min",
        "useRTH": True,
    }
    return {
        stream: ib.reqHistoricalData(contract, whatToShow=stream, **common)
        for stream in streams
    }


def print_historical_bars(tipo: str, bars_by_type: dict[str, list], required_streams: list[str] | None = None) -> None:
    required_streams = required_streams or list(bars_by_type)
    missing_required = [name for name in required_streams if not bars_by_type.get(name)]
    if missing_required:
        raise HistoricalDataUnavailable(
            "IBKR returned no historical bars for "
            + ", ".join(missing_required)
            + ". Check market-data permissions, contract routing, and TWS error messages."
        )

    if tipo == "forex" and {"BID", "ASK", "MIDPOINT"}.issubset(bars_by_type):
        print("Ultimi 10 BID, ASK e MIDPOINT:")
        for bar_bid, bar_ask, bar_mid in zip(
            bars_by_type["BID"][-10:],
            bars_by_type["ASK"][-10:],
            bars_by_type["MIDPOINT"][-10:],
        ):
            print(
                f"{bar_bid.date}  "
                f"BID: O={bar_bid.open:.5f} H={bar_bid.high:.5f} L={bar_bid.low:.5f} C={bar_bid.close:.5f} V={int(bar_bid.volume)} | "
                f"ASK: O={bar_ask.open:.5f} H={bar_ask.high:.5f} L={bar_ask.low:.5f} C={bar_ask.close:.5f} V={int(bar_ask.volume)} | "
                f"MID: O={bar_mid.open:.5f} H={bar_mid.high:.5f} L={bar_mid.low:.5f} C={bar_mid.close:.5f} V={int(bar_mid.volume)}"
            )
        return

    if set(bars_by_type) == {"TRADES"}:
        print("Ultimi 10 TRADES:")
        for bar_tr in bars_by_type["TRADES"][-10:]:
            print(
                f"{bar_tr.date}  "
                f"TRADES: O={bar_tr.open:.5f} H={bar_tr.high:.5f} L={bar_tr.low:.5f} C={bar_tr.close:.5f} V={int(bar_tr.volume)}"
            )
        return

    print("Ultimi 10 TRADES, BID, ASK, MIDPOINT:")
    for bar_tr, bar_bid, bar_ask, bar_mid in zip(
        bars_by_type["TRADES"][-10:],
        bars_by_type["BID"][-10:],
        bars_by_type["ASK"][-10:],
        bars_by_type["MIDPOINT"][-10:],
    ):
        print(
            f"{bar_tr.date}  "
            f"TRADES: O={bar_tr.open:.5f} H={bar_tr.high:.5f} L={bar_tr.low:.5f} C={bar_tr.close:.5f} V={int(bar_tr.volume)} | "
            f"BID: O={bar_bid.open:.5f} H={bar_bid.high:.5f} L={bar_bid.low:.5f} C={bar_bid.close:.5f} V={int(bar_bid.volume)} | "
            f"ASK: O={bar_ask.open:.5f} H={bar_ask.high:.5f} L={bar_ask.low:.5f} C={bar_ask.close:.5f} V={int(bar_ask.volume)} | "
            f"MID: O={bar_mid.open:.5f} H={bar_mid.high:.5f} L={bar_mid.low:.5f} C={bar_mid.close:.5f} V={int(bar_mid.volume)}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download historical bars from IBKR.")
    parser.add_argument("asset_type", nargs="?", choices=["forex", "stock"])
    parser.add_argument("ticker", nargs="?")
    parser.add_argument(
        "--streams",
        nargs="+",
        choices=sorted(VALID_STREAMS),
        help="IBKR whatToShow streams. Defaults: forex=BID ASK MIDPOINT, stock=TRADES.",
    )
    parser.add_argument("--client-id", type=int, help="Override the configured IBKR client id for this run.")
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    args = build_parser().parse_args(argv[1:])
    if args.asset_type and args.ticker:
        args.asset_type = args.asset_type.strip().lower()
        args.ticker = args.ticker.strip().upper()
        return args

    args.asset_type = input("Vuoi scaricare dati Forex o Stock/Futures? [forex/stock]: ").strip().lower()
    args.ticker = input("Inserisci il ticker (es: EURUSD per forex, AAPL per stock): ").strip().upper()
    return args


def main(argv: list[str] | None = None) -> int:
    from ib_async import IB
    import ib_async

    args = argv if argv is not None else sys.argv
    parsed = parse_args(args)
    config = load_runtime_config(global_path="config/global.toml")
    streams = parsed.streams or default_streams(parsed.asset_type)

    ib = IB()
    client_id_offset = (parsed.client_id - config.ibkr.client_id) if parsed.client_id is not None else 0
    connect_ibkr(ib, config.ibkr, client_id_offset=client_id_offset)
    try:
        contract = build_contract(ib_async, parsed.asset_type, parsed.ticker)
        bars = fetch_historical_bars(ib, contract, streams)
        print_historical_bars(parsed.asset_type, bars, streams)
    except HistoricalDataUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        ib.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
