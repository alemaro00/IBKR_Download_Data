#=============================================================================================
# MAIN.PY - ORCHESTRATORE DELL'ECOSISTEMA IBKR
# Gestisce il Bot Telegram in background e lancia i moduli di estrazione dati a comando
#=============================================================================================

import os
import subprocess
import sys
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

def run_portfolio_bot():
    env = os.environ.copy()
    env["PYTHONPATH"] = SRC_DIR + os.pathsep + env.get("PYTHONPATH", "")
    # Aggiunto '-u' (unbuffered) per garantire che i log del bot compaiano subito a schermo
    subprocess.run([sys.executable, "-u", "-m", "modules.portfolio_monitoring"], cwd=BASE_DIR, env=env)

def main():
    print("\n" + "="*50)
    print("🚀 AVVIO ECOSISTEMA IBKR...")
    print("🤖 Avvio del Bot Telegram (Portfolio Monitoring) in background...")
    print("="*50)
    
    # Avvia il bot come demone: morirà automaticamente quando chiudiamo il main.py
    bot_thread = threading.Thread(target=run_portfolio_bot, daemon=True)
    bot_thread.start()

    # Diamo 1.5 secondi al bot per connettersi e stampare i suoi log senza sporcare il menu
    time.sleep(1.5)

    try:
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
                print("\nChiusura dell'intero ecosistema in corso...")
                break

            if scelta in ["1", "2", "3"]:
                # Validazione rigorosa dell'input
                tipo = ""
                while tipo not in ["forex", "stock"]:
                    tipo = input("Vuoi operare su Forex o Stock? [forex/stock]: ").strip().lower()
                    if tipo not in ["forex", "stock"]:
                        print("⚠️ Errore: Devi digitare esattamente 'forex' o 'stock'.")
                        
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
                    print(f"\n--- TRANSIZIONE AI DATI LIVE PER {ticker} ---")
                    subprocess.run([sys.executable, "-m", "modules.realtime_data", tipo, ticker], cwd=BASE_DIR, env=env)
            else:
                print("\n⚠️ Scelta non valida. Riprova.")

    except KeyboardInterrupt:
        # Se premi Ctrl+C, il programma si chiude in modo pulito invece di mostrare errori
        print("\n\nInterruzione manuale rilevata (Ctrl+C). Chiusura ecosistema in corso...")
        
    finally:
        print("Ecosistema terminato con successo. Arrivederci! 👋")

if __name__ == "__main__":
    main()