#=============================================================================================

#Per vedere tutte le funzioni disponibili dentro la libreria ib_async quindi Stock, Forex, reqHistoricalData, etc
#import ib_async
#print(dir(ib_async)) 

#=============================================================================================
import os
import subprocess
import sys
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

def run_portfolio_bot():
    env = os.environ.copy()
    env["PYTHONPATH"] = SRC_DIR + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, "-m", "modules.portfolio_monitoring"], cwd=BASE_DIR, env=env)

def main():
    print("Avvio dell'ecosistema IBKR...")
    print("Avvio del Bot Telegram (Portfolio Monitoring) in background...")
    
    bot_thread = threading.Thread(target=run_portfolio_bot, daemon=True)
    bot_thread.start()

    while True:
        print("\n" + "="*45)
        print("📈 MENU PRINCIPALE - INTERACTIVE BROKERS 📉")
        print("="*45)
        print("1. Scarica Dati Storici (historical_data.py)")
        print("2. Visualizza Dati Live (realtime_data.py)")
        print("3. Storico + Live (Flusso continuo)")
        print("4. Esci (Chiude anche il bot e l'ecosistema)")
        print("="*45)
        
        scelta = input("\nSeleziona un'opzione (1, 2, 3 o 4): ").strip()

        if scelta == "4":
            print("\nChiusura dell'intero ecosistema...")
            break

        if scelta in ["1", "2", "3"]:
            # Chiediamo i dati centralmente SOLO se ha scelto 1, 2 o 3
            tipo = input("Vuoi operare su Forex o Stock/Futures? [forex/stock]: ").strip().lower()
            ticker = input("Inserisci il ticker (es: EURUSD o AAPL): ").strip().upper()
            
            env = os.environ.copy()
            env["PYTHONPATH"] = SRC_DIR + os.pathsep + env.get("PYTHONPATH", "")

            if scelta == "1":
                print(f"\n--- AVVIO DOWNLOAD DATI STORICI PER {ticker} ---")
                subprocess.run([sys.executable, "-m", "modules.historical_data", tipo, ticker], cwd=BASE_DIR, env=env)
            
            elif scelta == "2":
                print(f"\n--- AVVIO DATI LIVE PER {ticker} ---")
                subprocess.run([sys.executable, "-m", "modules.realtime_data", tipo, ticker], cwd=BASE_DIR, env=env)
                
            elif scelta == "3":
                print(f"\n--- AVVIO DATI STORICI E LIVE PER {ticker} ---")
                # 1. Avvia prima i dati storici
                subprocess.run([sys.executable, "-m", "modules.historical_data", tipo, ticker], cwd=BASE_DIR, env=env)
                
                # 2. Appena lo storico ha finito, attacca subito con il live
                print(f"--- TRANSIZIONE AI DATI LIVE PER {ticker} ---")
                subprocess.run([sys.executable, "-m", "modules.realtime_data", tipo, ticker], cwd=BASE_DIR, env=env)
        else:
            print("\nScelta non valida. Riprova.")

if __name__ == "__main__":
    main()