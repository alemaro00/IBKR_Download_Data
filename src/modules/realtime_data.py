#==============================================================================================

# CODICE RUNNABILE SENZA MAIN.PY, PER MONITORARE I DATI LIVE DI FOREX O STOCK/FUTURES

#==============================================================================================
from ib_async import *
import datetime
import sys  # Aggiunto per leggere gli argomenti dal main.py

ib = IB()
# Uso clientId=2 per evitare conflitti con portfolio_monitoring
ib.connect("127.0.0.1", 7497, clientId=2) 

# --- Lettura Input ---
if len(sys.argv) > 2:
    tipo = sys.argv[1].strip().lower()
    ticker = sys.argv[2].strip().upper()
else:
    tipo = input("Vuoi seguire dati live Forex o Stock/Futures? [forex/stock]: ").strip().lower()
    ticker = input("Inserisci il ticker (es: EURUSD per forex, AAPL per stock): ").strip().upper()

if tipo == "forex":
    contract = Forex(ticker)
else:
    contract = Stock(ticker, "SMART", "USD")

ib.qualifyContracts(contract)
tickerlive = ib.reqMktData(contract, '', False, False)

try:
    while True:
        live_bid = []
        live_ask = []
        live_mid = []
        start = datetime.datetime.now()
        
        # 1. Cattura il volume giornaliero all'INIZIO del minuto
        vol_val = tickerlive.volume
        # Controlliamo che il volume esista e non sia 'nan'
        start_vol = vol_val if vol_val is not None and str(vol_val) != 'nan' else 0
        
        for i in range(60):
            ib.sleep(1)
            if tickerlive.bid is not None and tickerlive.ask is not None:
                if tickerlive.bid > 0 and tickerlive.ask > 0:
                    live_bid.append(tickerlive.bid)
                    live_ask.append(tickerlive.ask)
                    live_mid.append((tickerlive.bid + tickerlive.ask) / 2)
            
            now = datetime.datetime.now()
            # Se manca meno di 1 secondo al prossimo minuto, esci subito
            if (now - start).seconds >= 60 or now.second == 0:
                break
                
        # Calcola O/H/L/C/V per BID, ASK, MID
        if live_bid and live_ask and live_mid:
            now = datetime.datetime.now().replace(second=0, microsecond=0)
            
            bid_o, bid_h, bid_l, bid_c = live_bid[0], max(live_bid), min(live_bid), live_bid[-1]
            ask_o, ask_h, ask_l, ask_c = live_ask[0], max(live_ask), min(live_ask), live_ask[-1]
            mid_o, mid_h, mid_l, mid_c = live_mid[0], max(live_mid), min(live_mid), live_mid[-1]
            
            # 2. Cattura il volume giornaliero alla FINE del minuto
            vol_val = tickerlive.volume
            end_vol = vol_val if vol_val is not None and str(vol_val) != 'nan' else 0
            
            # 3. Il volume della candela di 1 min è la differenza!
            candle_vol = int(end_vol - start_vol)
            if candle_vol < 0: 
                candle_vol = 0 # Evita numeri negativi se IBKR resetta i contatori a mezzanotte
                
            # Formattiamo la stringa: Se il volume non c'è (es. Forex), scriviamo N/A
            v_str = str(candle_vol) if end_vol > 0 else "N/A"
            
            # 4. Cattura le Size (contratti in attesa nei book) per BID e ASK se disponibili
            b_size = int(tickerlive.bidSize) if tickerlive.bidSize is not None and str(tickerlive.bidSize) != 'nan' else "N/A"
            a_size = int(tickerlive.askSize) if tickerlive.askSize is not None and str(tickerlive.askSize) != 'nan' else "N/A"

            # 5. Stampa a schermo con i nuovi valori
            print(
                f"{now:%Y-%m-%d %H:%M:%S}  "
                f"BID: O={bid_o:.5f} H={bid_h:.5f} L={bid_l:.5f} C={bid_c:.5f} Size={b_size} | "
                f"ASK: O={ask_o:.5f} H={ask_h:.5f} L={ask_l:.5f} C={ask_c:.5f} Size={a_size} | "
                f"MID: O={mid_o:.5f} H={mid_h:.5f} L={mid_l:.5f} C={mid_c:.5f} V={v_str}"
            )
        else:
             print(f"{datetime.datetime.now():%H:%M:%S} - Attesa dati dal mercato...")
             
except KeyboardInterrupt:
    print("\nInterrotto dall'utente.")
finally:
    ib.disconnect()
    print("Disconnesso da IBKR.")