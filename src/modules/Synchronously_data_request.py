#=============================================================================================

#Per vedere tutte le funzioni disponibili dentro la libreria ib_async quindi Stock, Forex, reqHistoricalData, etc
#import ib_async
#print(dir(ib_async)) 

#=============================================================================================

from ib_async import *
import datetime
import pytz

ib = IB()
ib.connect("127.0.0.1", 7497, clientId=1)

# --- Interazione utente ---
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


# --- Live market data aggregato come storico per 5 minuti ---
ib.qualifyContracts(contract)
tickerlive = ib.reqMktData(contract, '', False, False)

while True:
    live_bid = []
    live_ask = []
    live_mid = []
    start = datetime.datetime.now()
    for i in range(60):
        ib.sleep(1)
        if tickerlive.bid is not None and tickerlive.ask is not None:
            live_bid.append(tickerlive.bid)
            live_ask.append(tickerlive.ask)
            live_mid.append((tickerlive.bid + tickerlive.ask) / 2)
        now = datetime.datetime.now()
        # Se manca meno di 1 secondo al prossimo minuto, esci subito
        if (now - start).seconds >= 60 or now.second == 0:
            break
    # Calcola O/H/L/C/V per BID, ASK, MID
    if live_bid and live_ask and live_mid:
        # Arrotonda timestamp al minuto corrente
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        bid_o = live_bid[0]
        bid_h = max(live_bid)
        bid_l = min(live_bid)
        bid_c = live_bid[-1]
        ask_o = live_ask[0]
        ask_h = max(live_ask)
        ask_l = min(live_ask)
        ask_c = live_ask[-1]
        mid_o = live_mid[0]
        mid_h = max(live_mid)
        mid_l = min(live_mid)
        mid_c = live_mid[-1]
        # Volume non disponibile in live, metti -1
        print(
            f"{now:%Y-%m-%d %H:%M:%S}  "
            f"BID: O={bid_o:.5f} H={bid_h:.5f} L={bid_l:.5f} C={bid_c:.5f} V=-1 | "
            f"ASK: O={ask_o:.5f} H={ask_h:.5f} L={ask_l:.5f} C={ask_c:.5f} V=-1 | "
            f"MID: O={mid_o:.5f} H={mid_h:.5f} L={mid_l:.5f} C={mid_c:.5f} V=-1")

ib.disconnect()