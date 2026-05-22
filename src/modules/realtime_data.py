#=============================================================================================

#Per vedere tutte le funzioni disponibili dentro la libreria ib_async quindi Stock, Forex, reqHistoricalData, etc
#import ib_async
#print(dir(ib_async)) 

#=============================================================================================

from ib_async import *
import datetime
import pytz
from modules.historycal_data import contract

ib = IB()
ib.connect("127.0.0.1", 7497, clientId=1)

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