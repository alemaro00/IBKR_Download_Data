#==============================================================================================
# CODICE PER SCARICARE I DATI STORICI DI FOREX O STOCK
# Ottimizzato per la creazione di dataset, con supporto a Ticker testuali e Contract ID
#==============================================================================================

import sys
import random
import pandas as pd
from ib_async import IB, Forex, Stock, Contract, util

def get_historical_data(tipo: str, ticker: str):
    ib = IB()
    
    # 1. RISOLUZIONE CONFLITTI: Generiamo un clientId casuale. 
    client_id = random.randint(100, 9999)
    
    try:
        ib.connect("127.0.0.1", 7497, clientId=client_id)
    except Exception as e:
        print(f"Errore di connessione a IBKR: {e}")
        return None

    # 2. DEFINIZIONE DEL CONTRATTO (Intelligente: Ticker o Contract ID)
    if ticker.isdigit():
        print(f"\nRilevato Contract ID: {ticker}. Risoluzione dello strumento in corso...")
        contract = Contract(conId=int(ticker))
    else:
        if tipo == "forex":
            contract = Forex(ticker)
        else:
            contract = Stock(ticker, "SMART", "USD")

    # 3. VALIDAZIONE DEL CONTRATTO
    try:
        # qualifyContracts cerca il ticker sui server IBKR e popola tutti i dettagli
        ib.qualifyContracts(contract)
        
        # Se non trova nulla, il conId rimane a 0
        if getattr(contract, 'conId', 0) == 0:
            print(f"\n❌ Errore: Nessuno strumento trovato per l'input '{ticker}'.")
            return None
            
        # Conferma visiva se l'utente ha usato un ID numerico
        if ticker.isdigit():
            print(f"✅ Strumento identificato: {contract.symbol} ({contract.secType}) su {contract.primaryExchange}")
            
    except Exception as e:
        print(f"\n❌ Errore durante la validazione del contratto: {e}")
        return None

    print(f"\nScaricamento dati storici per {contract.symbol}...")

    # Impostazioni comuni per il download
    kwargs = {
        "endDateTime": "",
        "durationStr": "1 M",          # Storico di 1 mese
        "barSizeSetting": "1 hour",    # Candele da 1 ora
        "useRTH": False                # False = include Pre-Market e After-Market
    }
    

    try:
        if tipo == "forex" or contract.secType == "CASH":
            # Il Forex non ha "TRADES", quindi scarichiamo solo BID, ASK, MIDPOINT
            bars_bid = ib.reqHistoricalData(contract, whatToShow="BID", **kwargs)
            bars_ask = ib.reqHistoricalData(contract, whatToShow="ASK", **kwargs)
            bars_mid = ib.reqHistoricalData(contract, whatToShow="MIDPOINT", **kwargs)
            
            if not (bars_bid and bars_ask and bars_mid):
                print("Dati insufficienti restituiti da IBKR.")
                return None

            # CREAZIONE DATASET SICURO CON PANDAS
            df_bid = util.df(bars_bid)[['date', 'open', 'high', 'low', 'close', 'volume']].add_suffix('_BID')
            df_ask = util.df(bars_ask)[['date', 'open', 'high', 'low', 'close', 'volume']].add_suffix('_ASK')
            df_mid = util.df(bars_mid)[['date', 'open', 'high', 'low', 'close', 'volume']].add_suffix('_MID')

            df = df_bid.rename(columns={'date_BID': 'date'}) \
                .merge(df_ask.rename(columns={'date_ASK': 'date'}), on='date', how='outer') \
                .merge(df_mid.rename(columns={'date_MID': 'date'}), on='date', how='outer') \
                .sort_values('date')

        else:
            # Per Stock scarichiamo anche i TRADES (Scambi effettivi)
            bars_trades = ib.reqHistoricalData(contract, whatToShow="TRADES", **kwargs)
            bars_bid = ib.reqHistoricalData(contract, whatToShow="BID", **kwargs)
            bars_ask = ib.reqHistoricalData(contract, whatToShow="ASK", **kwargs)
            bars_mid = ib.reqHistoricalData(contract, whatToShow="MIDPOINT", **kwargs)

            if not (bars_trades and bars_bid and bars_ask and bars_mid):
                print("Dati insufficienti restituiti da IBKR.")
                return None

            df_tr = util.df(bars_trades)[['date', 'open', 'high', 'low', 'close', 'volume']].add_suffix('_TR')
            df_bid = util.df(bars_bid)[['date', 'open', 'high', 'low', 'close', 'volume']].add_suffix('_BID')
            df_ask = util.df(bars_ask)[['date', 'open', 'high', 'low', 'close', 'volume']].add_suffix('_ASK')
            df_mid = util.df(bars_mid)[['date', 'open', 'high', 'low', 'close', 'volume']].add_suffix('_MID')

            df = df_tr.rename(columns={'date_TR': 'date'}) \
                .merge(df_bid.rename(columns={'date_BID': 'date'}), on='date', how='outer') \
                .merge(df_ask.rename(columns={'date_ASK': 'date'}), on='date', how='outer') \
                .merge(df_mid.rename(columns={'date_MID': 'date'}), on='date', how='outer') \
                .sort_values('date')

        print(f"\nEstrazione completata. {len(df)} righe elaborate.")
        print("\nStampa di TUTTO il dataset:")
        
        # Usa option_context per rimuovere temporaneamente i limiti di stampa di Pandas
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(df.tail().to_string(index=False))

        # ESPORTAZIONE PER DATASET (De-commenta le righe sotto per salvare in CSV)
        file_name = f"{contract.symbol}_{tipo}_historical.csv"
        df.to_csv(file_name, index=False)
        print(f"\nDati salvati con successo in: {file_name}")

        return df

    except Exception as e:
        print(f"Si è verificato un errore durante l'estrazione: {e}")
        return None

    finally:
        ib.disconnect()

# ==============================================================================================
# ESECUZIONE ISOLATA
# ==============================================================================================
if __name__ == "__main__":
    if len(sys.argv) > 2:
        arg_tipo = sys.argv[1].strip().lower()
        arg_ticker = sys.argv[2].strip().upper()
    else:
        arg_tipo = input("Vuoi scaricare dati Forex o Stock? [forex/stock]: ").strip().lower()
        arg_ticker = input("Inserisci il ticker testuale (es: AAPL) o il Contract ID numerico: ").strip().upper()
    
    get_historical_data(arg_tipo, arg_ticker)