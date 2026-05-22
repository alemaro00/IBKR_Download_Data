#==============================================================================================

# CODICE RUNNABILE SENZA MAIN.PY, PER MONITORARE IL PORTAFOGLIO IN TEMPO REALE CON UN BOT TELEGRAM

#==============================================================================================

import sys
import os

# ---- FIX PER IL RUN DIRETTO ----
# Aggiunge la cartella 'src' ai percorsi di Python così riconosce il pacchetto 'modules'
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, ".."))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
# --------------------------------

import asyncio
from ib_async import IB
from telegram.ext import ApplicationBuilder, CommandHandler
from trading.config import load_runtime_config
from trading.ibkr import connect_ibkr_async
from modules.telegram_messages import (
    TELEGRAM_BOT_TOKEN,
    send_async_portfolio_update,
    help_command,
    posizioni_command,
    pnl_command,
    tutto_command
)
# Ciclo di monitoraggio in background (Task 1)
async def monitor_loop(ib, telegram_app):
    account = ib.managedAccounts()[0]
    # Sottoscrizione al flusso P&L continuo di IBKR
    pnl_subscription = ib.reqPnL(account)
    
#    print("Avvio ciclo di monitoraggio automatico (Ogni 1 ora)...")
    try:
        while True:
            # Aspetta un'ora cedendo il controllo ad altri task (es. i comandi Telegram)
            await asyncio.sleep(3600) 
            
            positions = ib.positions()
            orders = ib.openTrades()
            
#            print(f"Esecuzione report automatico pianificato: {len(positions)} posizioni trovate.")
            
            # Inviamo l'aggiornamento automatico usando il bot interno all'applicazione telegram
            await send_async_portfolio_update(telegram_app.bot, positions, orders, pnl_subscription)
            
    except asyncio.CancelledError:
        print("Ciclo di monitoraggio interrotto.")

# Funzione Principale Asincrona
async def main():
    # 1. Inizializza e connette IBKR in modalità asincrona
    config = load_runtime_config(global_path="config/global.toml")
    ib = IB()
#    print("Connessione a IBKR in corso...")
    await connect_ibkr_async(ib, config.ibkr, client_id_offset=2)
    
    # 2. Configura l'applicazione Telegram (Task 2)
    # TELEGRAM_BOT_TOKEN arriva già popolato dal file .env grazie all'import iniziale
    telegram_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Salviamo l'istanza 'ib' dentro i dati del bot, 
    # così i comandi /posizioni o /pnl possono leggerla in qualsiasi momento
    telegram_app.bot_data['ib_instance'] = ib
    
    # Registriamo i comandi che l'utente può digitare su Telegram
    telegram_app.add_handler(CommandHandler("start", help_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("posizioni", posizioni_command))
    telegram_app.add_handler(CommandHandler("pnl", pnl_command))
    telegram_app.add_handler(CommandHandler("tutto", tutto_command))
    
    # 3. Avviamo Telegram in background senza bloccare il codice
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
#    print("Bot Telegram attivo e in ascolto dei comandi...")
    
    # 4. Creiamo il task per il ciclo di monitoraggio orario di IBKR
    monitor_task = asyncio.create_task(monitor_loop(ib, telegram_app))
    
    # 5. Manteniamo l'applicazione attiva coordinando i flussi di IBKR e Telegram
    try:
        while True:
            # Esegue l'ascolto degli eventi di rete interni di IBKR
            await asyncio.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        print("Spegnimento in corso...")
    finally:
        # Chiusura pulita di tutti i servizi
        monitor_task.cancel()
        await telegram_app.updater.stop()
        await telegram_app.stop()
        ib.disconnect()

if __name__ == "__main__":
    # Avvia l'Event Loop nativo di Python
    asyncio.run(main())
