#==============================================================================================
# CODICE PER MONITORARE IL PORTAFOGLIO IN TEMPO REALE CON UN BOT TELEGRAM
# Esecuzione asincrona indipendente per ecosistema IBKR
#==============================================================================================

import sys
import os
import asyncio
from ib_async import IB
from telegram.ext import ApplicationBuilder, CommandHandler

# ---- FIX PER IL RUN DIRETTO ----
# Aggiunge la cartella 'src' ai percorsi di Python così riconosce il pacchetto 'modules'
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, ".."))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
# --------------------------------

from modules.telegram_messages import (
    TELEGRAM_BOT_TOKEN,
    send_async_portfolio_update,
    help_command,
    posizioni_command,
    pnl_command,
    tutto_command
)

# --- TASK 1: Ciclo di monitoraggio in background ---
async def monitor_loop(ib, telegram_app, account):
    # Sottoscrizione al flusso P&L continuo di IBKR
    pnl_subscription = ib.reqPnL(account)
    
    try:
        while True:
            # Aspetta un'ora (3600 secondi) cedendo il controllo ad altri task
            await asyncio.sleep(3600) 
            
            positions = ib.positions()
            orders = ib.openTrades()
            
            # Inviamo l'aggiornamento automatico usando il bot interno all'applicazione Telegram
            await send_async_portfolio_update(telegram_app.bot, positions, orders, pnl_subscription)
            
    except asyncio.CancelledError:
        print("Ciclo di monitoraggio automatico interrotto.")


# --- TASK PRINCIPALE: Orchestrazione IBKR e Telegram ---
async def main():
    # 1. Inizializza e connette IBKR in modalità asincrona (uso esclusivo di clientId=3 per il bot)
    ib = IB()
    try:
        await ib.connectAsync("127.0.0.1", 7497, clientId=3)
    except Exception as e:
        print(f"Errore critico: Impossibile connettere il bot a IBKR. Dettagli: {e}")
        return
    
    # ATTESA DI SICUREZZA: Previene IndexError se IBKR ritarda l'invio dei dati del conto
    while not ib.managedAccounts():
        await asyncio.sleep(0.1)
    
    # Ora è sicuro estrarre l'account
    account = ib.managedAccounts()[0]
    
    # 2. Configura l'applicazione Telegram
    telegram_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Salviamo l'istanza 'ib' dentro i dati del bot per renderla accessibile ai comandi On-Demand
    telegram_app.bot_data['ib_instance'] = ib
    
    # Registriamo i comandi
    telegram_app.add_handler(CommandHandler("start", help_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("posizioni", posizioni_command))
    telegram_app.add_handler(CommandHandler("pnl", pnl_command))
    telegram_app.add_handler(CommandHandler("tutto", tutto_command))
    
    # 3. Avviamo Telegram in background
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    
    # 4. Creiamo il task per il ciclo di monitoraggio orario di IBKR
    # Passiamo 'account' al loop in modo pulito
    monitor_task = asyncio.create_task(monitor_loop(ib, telegram_app, account))
    
    # 5. Manteniamo l'applicazione attiva coordinando i flussi asincroni
    try:
        while True:
            # Esegue l'ascolto degli eventi di rete interni di IBKR
            await asyncio.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        print("\nSpegnimento del bot Telegram e disconnessione IBKR in corso...")
    finally:
        # Chiusura pulita di tutti i servizi per evitare ghost-process
        monitor_task.cancel()
        await telegram_app.updater.stop()
        await telegram_app.stop()
        ib.disconnect()

if __name__ == "__main__":
    # Avvia l'Event Loop nativo di Python
    asyncio.run(main())