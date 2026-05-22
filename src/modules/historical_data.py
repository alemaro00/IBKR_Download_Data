#==============================================================================================

# CODICE RUNNABILE SENZA MAIN.PY, PER SCARICARE I DATI STORICI DI FOREX O STOCK/FUTURES

#==============================================================================================

from ib_async import *
import datetime
import pytz
import sys  # Aggiunto per leggere gli argomenti dal main.py

ib = IB()
ib.connect("127.0.0.1", 7497, clientId=1)

# --- Lettura Input ---
# Se passiamo gli argomenti dal main.py li usiamo, altrimenti chiediamo l'input (fallback)
if len(sys.argv) > 2:
    tipo = sys.argv[1].strip().lower()
    ticker = sys.argv[2].strip().upper()
else:
    tipo = input("Vuoi scaricare dati Forex o Stock/Futures? [forex/stock]: ").strip().lower()
    ticker = input("Inserisci il ticker (es: EURUSD per forex, AAPL per stock): ").strip().upper()

if tipo == "forex":
    contract = Forex(ticker)
    bars_bid = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="1 min",
        whatToShow="BID",
        useRTH=True
    )
    bars_ask = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="1 min",
        whatToShow="ASK",
        useRTH=True
    )
    bars_mid = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="1 min",
        whatToShow="MIDPOINT",
        useRTH=True
    )
    print("Ultimi 10 BID, ASK e MIDPOINT:")
    for bar_bid, bar_ask, bar_mid in zip(bars_bid[-10:], bars_ask[-10:], bars_mid[-10:]):
        print(
            f"{bar_bid.date}  "
            f"BID: O={bar_bid.open:.5f} H={bar_bid.high:.5f} L={bar_bid.low:.5f} C={bar_bid.close:.5f} V={int(bar_bid.volume)} | "
            f"ASK: O={bar_ask.open:.5f} H={bar_ask.high:.5f} L={bar_ask.low:.5f} C={bar_ask.close:.5f} V={int(bar_ask.volume)} | "
            f"MID: O={bar_mid.open:.5f} H={bar_mid.high:.5f} L={bar_mid.low:.5f} C={bar_mid.close:.5f} V={int(bar_mid.volume)}"
        )
else:
    contract = Stock(ticker, "SMART", "USD")
    bars_trades = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="1 min",
        whatToShow="TRADES",
        useRTH=True
    )
    bars_bid = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="1 min",
        whatToShow="BID",
        useRTH=True
    )
    bars_ask = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="1 min",
        whatToShow="ASK",
        useRTH=True
    )
    bars_mid = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="1 min",
        whatToShow="MIDPOINT",
        useRTH=True
    )
    print("Ultimi 10 TRADES, BID, ASK, MIDPOINT:")
    for bar_tr, bar_bid, bar_ask, bar_mid in zip(bars_trades[-10:], bars_bid[-10:], bars_ask[-10:], bars_mid[-10:]):
        print(
            f"{bar_tr.date}  "
            f"TRADES: O={bar_tr.open:.5f} H={bar_tr.high:.5f} L={bar_tr.low:.5f} C={bar_tr.close:.5f} V={int(bar_tr.volume)} | "
            f"BID: O={bar_bid.open:.5f} H={bar_bid.high:.5f} L={bar_bid.low:.5f} C={bar_bid.close:.5f} V={int(bar_bid.volume)} | "
            f"ASK: O={bar_ask.open:.5f} H={bar_ask.high:.5f} L={bar_ask.low:.5f} C={bar_ask.close:.5f} V={int(bar_ask.volume)} | "
            f"MID: O={bar_mid.open:.5f} H={bar_mid.high:.5f} L={bar_mid.low:.5f} C={bar_mid.close:.5f} V={int(bar_mid.volume)}"
        )

ib.disconnect()