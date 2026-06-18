#==============================================================================================
# CODICE PER MONITORARE I DATI LIVE DI FOREX O STOCK
# Ottimizzato per l'integrazione, con supporto a Ticker testuali e Contract ID
#==============================================================================================

import sys
import datetime
import random
from ib_async import IB, Forex, Stock, Contract

def stream_realtime_data(tipo: str, ticker: str):
    ib = IB()
    
    # 1. RISOLUZIONE CONFLITTI: Generiamo un clientId casuale per evitare sovrapposizioni
    # con il bot di monitoraggio (clientId=3) o con i download storici.
    client_id = random.randint(100, 9999)
    
    try:
        print(f"\nConnessione a IBKR (Live Stream) con clientId={client_id}...")
        ib.connect("127.0.0.1", 7497, clientId=client_id)
    except Exception as e:
        print(f"Errore di connessione a IBKR nel modulo Realtime: {e}")
        return

    # 2. DEFINIZIONE DEL CONTRATTO (Intelligente: Ticker o Contract ID)
    if ticker.isdigit():
        print(f"Rilevato Contract ID: {ticker}. Risoluzione dello strumento in corso...")
        contract = Contract(conId=int(ticker))
    else:
        if tipo == "forex":
            contract = Forex(ticker)
        else:
            contract = Stock(ticker, "SMART", "USD")

    # 3. VALIDAZIONE DEL CONTRATTO
    try:
        ib.qualifyContracts(contract)
        
        # Se dopo la ricerca il conId rimane 0, lo strumento non esiste
        if getattr(contract, 'conId', 0) == 0:
            print(f"\n❌ Errore: Nessuno strumento trovato per l'input '{ticker}'.")
            ib.disconnect()
            return
            
        # Conferma visiva se l'utente ha usato un ID numerico
        if ticker.isdigit():
            print(f"✅ Strumento identificato: {contract.symbol} ({contract.secType}) su {contract.primaryExchange}")
            
    except Exception as e:
        print(f"\n❌ Errore: Contratto per {ticker} non valido o ambiguo. Dettagli: {e}")
        ib.disconnect()
        return

    print(f"\nSottoscrizione dati di mercato in tempo reale per: {contract.symbol}...\n")
    tickerlive = ib.reqMktData(contract, '', False, False)

    # 4. CICLO DI LETTURA E COSTRUZIONE CANDELE A 1 MINUTO
    try:
        while True:
            live_bid = []
            live_ask = []
            live_mid = []
            start = datetime.datetime.now()
            
            # Cattura il volume giornaliero all'INIZIO del minuto
            vol_val = tickerlive.volume
            start_vol = vol_val if vol_val is not None and str(vol_val) != 'nan' else 0
            
            # Ciclo di campionamento di 60 secondi
            for i in range(60):
                ib.sleep(1)
                
                # Se i dati Bid/Ask sono validi, li registriamo
                if tickerlive.bid is not None and tickerlive.ask is not None:
                    if tickerlive.bid > 0 and tickerlive.ask > 0:
                        live_bid.append(tickerlive.bid)
                        live_ask.append(tickerlive.ask)
                        live_mid.append((tickerlive.bid + tickerlive.ask) / 2)
                
                now = datetime.datetime.now()
                # Usciamo dal campionamento se è passato 1 minuto o scocca il minuto tondo
                if (now - start).seconds >= 60 or now.second == 0:
                    break
                    
            # Calcola Open, High, Low, Close (O/H/L/C) per la candela
            if live_bid and live_ask and live_mid:
                now = datetime.datetime.now().replace(second=0, microsecond=0)
                
                bid_o, bid_h, bid_l, bid_c = live_bid[0], max(live_bid), min(live_bid), live_bid[-1]
                ask_o, ask_h, ask_l, ask_c = live_ask[0], max(live_ask), min(live_ask), live_ask[-1]
                mid_o, mid_h, mid_l, mid_c = live_mid[0], max(live_mid), min(live_mid), live_mid[-1]
                
                # Cattura il volume giornaliero alla FINE del minuto
                vol_val = tickerlive.volume
                end_vol = vol_val if vol_val is not None and str(vol_val) != 'nan' else 0
                
                # Il volume della candela a 1 min è la differenza
                candle_vol = int(end_vol - start_vol)
                if candle_vol < 0: 
                    candle_vol = 0 
                    
                v_str = str(candle_vol) if end_vol > 0 else "N/A"
                
                # Cattura le Size (contratti in attesa nei book)
                b_size = int(tickerlive.bidSize) if tickerlive.bidSize is not None and str(tickerlive.bidSize) != 'nan' else "N/A"
                a_size = int(tickerlive.askSize) if tickerlive.askSize is not None and str(tickerlive.askSize) != 'nan' else "N/A"

                # Stampa a schermo formattata
                print(
                    f"{now:%Y-%m-%d %H:%M:%S}  "
                    f"BID: O={bid_o:.5f} H={bid_h:.5f} L={bid_l:.5f} C={bid_c:.5f} Size={b_size} | "
                    f"ASK: O={ask_o:.5f} H={ask_h:.5f} L={ask_l:.5f} C={ask_c:.5f} Size={a_size} | "
                    f"MID: O={mid_o:.5f} H={mid_h:.5f} L={mid_l:.5f} C={mid_c:.5f} V={v_str}"
                )
            else:
                print(f"{datetime.datetime.now():%H:%M:%S} - In attesa di dati dal mercato...")
                 
    except KeyboardInterrupt:
        print("\nFlusso real-time interrotto dall'utente (Ctrl+C).")
    finally:
        ib.disconnect()
        print("Disconnesso da IBKR per la sessione Realtime.")

# ==============================================================================================
# ESECUZIONE ISOLATA
# ==============================================================================================
if __name__ == "__main__":
    if len(sys.argv) > 2:
        arg_tipo = sys.argv[1].strip().lower()
        arg_ticker = sys.argv[2].strip().upper()
    else:
        arg_tipo = input("Vuoi seguire dati live Forex o Stock? [forex/stock]: ").strip().lower()
        arg_ticker = input("Inserisci il ticker testuale (es: AAPL) o il Contract ID numerico: ").strip().upper()
    
    stream_realtime_data(arg_tipo, arg_ticker)