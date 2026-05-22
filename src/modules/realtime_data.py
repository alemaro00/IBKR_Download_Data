from __future__ import annotations

import datetime
import sys

from trading.config import load_runtime_config
from trading.ibkr import connect_ibkr


def parse_args(argv: list[str]) -> tuple[str, str]:
    if len(argv) > 2:
        return argv[1].strip().lower(), argv[2].strip().upper()
    tipo = input("Vuoi seguire dati live Forex o Stock/Futures? [forex/stock]: ").strip().lower()
    ticker = input("Inserisci il ticker (es: EURUSD per forex, AAPL per stock): ").strip().upper()
    return tipo, ticker


def build_contract(ib_module, tipo: str, ticker: str):
    if tipo == "forex":
        return ib_module.Forex(ticker)
    return ib_module.Stock(ticker, "SMART", "USD")


def collect_one_minute_candle(ib, tickerlive) -> str:
    live_bid = []
    live_ask = []
    live_mid = []
    start = datetime.datetime.now()

    vol_val = tickerlive.volume
    start_vol = vol_val if vol_val is not None and str(vol_val) != "nan" else 0

    for _ in range(60):
        ib.sleep(1)
        if tickerlive.bid is not None and tickerlive.ask is not None:
            if tickerlive.bid > 0 and tickerlive.ask > 0:
                live_bid.append(tickerlive.bid)
                live_ask.append(tickerlive.ask)
                live_mid.append((tickerlive.bid + tickerlive.ask) / 2)

        now = datetime.datetime.now()
        if (now - start).seconds >= 60 or now.second == 0:
            break

    if not live_bid or not live_ask or not live_mid:
        return f"{datetime.datetime.now():%H:%M:%S} - Attesa dati dal mercato..."

    now = datetime.datetime.now().replace(second=0, microsecond=0)
    bid_o, bid_h, bid_l, bid_c = live_bid[0], max(live_bid), min(live_bid), live_bid[-1]
    ask_o, ask_h, ask_l, ask_c = live_ask[0], max(live_ask), min(live_ask), live_ask[-1]
    mid_o, mid_h, mid_l, mid_c = live_mid[0], max(live_mid), min(live_mid), live_mid[-1]

    vol_val = tickerlive.volume
    end_vol = vol_val if vol_val is not None and str(vol_val) != "nan" else 0
    candle_vol = int(end_vol - start_vol)
    if candle_vol < 0:
        candle_vol = 0
    v_str = str(candle_vol) if end_vol > 0 else "N/A"

    b_size = int(tickerlive.bidSize) if tickerlive.bidSize is not None and str(tickerlive.bidSize) != "nan" else "N/A"
    a_size = int(tickerlive.askSize) if tickerlive.askSize is not None and str(tickerlive.askSize) != "nan" else "N/A"

    return (
        f"{now:%Y-%m-%d %H:%M:%S}  "
        f"BID: O={bid_o:.5f} H={bid_h:.5f} L={bid_l:.5f} C={bid_c:.5f} Size={b_size} | "
        f"ASK: O={ask_o:.5f} H={ask_h:.5f} L={ask_l:.5f} C={ask_c:.5f} Size={a_size} | "
        f"MID: O={mid_o:.5f} H={mid_h:.5f} L={mid_l:.5f} C={mid_c:.5f} V={v_str}"
    )


def main(argv: list[str] | None = None) -> int:
    from ib_async import IB
    import ib_async

    args = argv if argv is not None else sys.argv
    tipo, ticker = parse_args(args)
    config = load_runtime_config(global_path="config/global.toml")

    ib = IB()
    connect_ibkr(ib, config.ibkr, client_id_offset=1)
    try:
        contract = build_contract(ib_async, tipo, ticker)
        ib.qualifyContracts(contract)
        tickerlive = ib.reqMktData(contract, "", False, False)
        while True:
            print(collect_one_minute_candle(ib, tickerlive))
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")
    finally:
        ib.disconnect()
        print("Disconnesso da IBKR.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
