import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Preleva le variabili in modo sicuro
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- HELPER FUNZIONI CONDIVISE ---

async def send_async_portfolio_update(bot, positions, orders, pnl_obj):
    """
    Invia il report automatico pianificato.
    Nota: pnl_obj qui è l'oggetto singolo restituito da ib.reqPnL()
    """
    msg = "📊 *Aggiornamento Portafoglio Automatico*\n\n"
    msg += format_portfolio_data(positions, orders, pnl_obj)
    
    # Usiamo la variabile recuperata dal file .env
    if TELEGRAM_CHAT_ID:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode='Markdown')
    else:
        print("Errore: TELEGRAM_CHAT_ID non trovato nel file .env")

def format_portfolio_data(positions, orders, pnl_obj) -> str:
    """
    Funzione di utilità condivisa per formattare i dati di IBKR.
    Si aspetta che pnl_obj sia un oggetto singolo (es. pnl_list[-1] o pnl_subscription)
    """
    msg = "💼 *Posizioni Correnti:*\n"
    if positions:
        for pos in positions:
            # Mostra ticker, quantità e prezzo medio di carico
            msg += f"• {pos.contract.symbol}: {pos.position} @ ${pos.avgCost:.2f}\n"
    else:
        msg += "Nessuna posizione aperta.\n"
        
    msg += f"\n📝 *Ordini Aperti:* {len(orders)}\n"
    if orders:
        for trade in orders:
            # Mostra ticker, azione (BUY/SELL) e quantità
            msg += f"• {trade.contract.symbol}: {trade.order.action} {trade.order.totalQuantity}\n"
    else:
        msg += "Nessun ordine in sospeso.\n"
        
    msg += "\n💰 *Profitto & Perdita (P&L):*\n"
    # Controlliamo che l'oggetto esista e abbia gli attributi giusti
    if pnl_obj:
        unrealized = getattr(pnl_obj, 'unrealizedPnL', 0.0)
        unrealized = unrealized if unrealized is not None else 0.0
        
        realized = getattr(pnl_obj, 'realizedPnL', 0.0)
        realized = realized if realized is not None else 0.0
        
        msg += f"Non Realizzato: ${unrealized:.2f}\nRealizzato: ${realized:.2f}\n"
    else:
        msg += "Dati P&L temporaneamente non disponibili.\n"
        
    return msg


# --- GESTORI DEI COMANDI TELEGRAM (On-Demand) ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Risponde al comando /help elencando i comandi disponibili."""
    text = (
        "🤖 *Comandi Disponibili Bot IBKR:*\n\n"
        "/help - Mostra questo messaggio di aiuto\n"
        "/posizioni - Mostra solo le posizioni aperte in tempo reale\n"
        "/pnl - Mostra il P&L aggiornato ad adesso\n"
        "/tutto - Mostra il report completo (Posizioni + Ordini + P&L)"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def posizioni_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Risponde al comando /posizioni leggendo l'istanza IB condivisa."""
    ib = context.bot_data['ib_instance'] # Recuperiamo IBKR condiviso
    positions = ib.positions()
    
    msg = "💼 *Posizioni Correnti (Real-time):*\n"
    if positions:
        for pos in positions:
            msg += f"• {pos.contract.symbol}: {pos.position} @ ${pos.avgCost:.2f}\n"
    else:
        msg += "Nessuna posizione aperta."
        
    await update.message.reply_text(msg, parse_mode='Markdown')

async def pnl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Risponde al comando /pnl."""
    ib = context.bot_data['ib_instance']
    
    # Recuperiamo l'account in modo sicuro
    accounts = ib.managedAccounts()
    if not accounts:
        await update.message.reply_text("⏳ Sincronizzazione con l'account in corso, riprova tra poco.")
        return
        
    account = accounts[0]
    
    # ib.pnl() restituisce una lista dei dati PnL attualmente in memoria
    pnl_list = ib.pnl(account) 
    
    msg = "💰 *P&L Attuale:*\n"
    # Protezione IndexError: controlliamo se la lista ha elementi
    if pnl_list and len(pnl_list) > 0:
        latest_pnl = pnl_list[-1]
        unrealized = getattr(latest_pnl, 'unrealizedPnL', 0.0)
        unrealized = unrealized if unrealized is not None else 0.0
        
        realized = getattr(latest_pnl, 'realizedPnL', 0.0)
        realized = realized if realized is not None else 0.0
        
        msg += f"Non Realizzato: ${unrealized:.2f}\nRealizzato: ${realized:.2f}"
    else:
        msg += "Dati P&L temporaneamente non disponibili o non ancora aggiornati da IBKR."
        
    await update.message.reply_text(msg, parse_mode='Markdown')

async def tutto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Risponde al comando /tutto richiedendo l'intero pacchetto informativo."""
    ib = context.bot_data['ib_instance']
    
    # Recuperiamo l'account in modo sicuro
    accounts = ib.managedAccounts()
    if not accounts:
        await update.message.reply_text("⏳ Sincronizzazione con l'account in corso, riprova tra poco.")
        return
        
    account = accounts[0]
    
    # Prende tutti i dati istantaneamente
    positions = ib.positions()
    orders = ib.openTrades()
    
    # reqPnL è già attivo in background grazie a portfolio_monitoring.py
    # Leggiamo l'ultimo valore disponibile dalla memoria
    pnl_list = ib.pnl(account)
    latest_pnl = pnl_list[-1] if pnl_list and len(pnl_list) > 0 else None
    
    # Sfruttiamo la funzione formattatrice passando il singolo oggetto PnL (o None)
    msg = "📊 *Report Portafoglio Istantaneo*\n\n" + format_portfolio_data(positions, orders, latest_pnl)
    
    await update.message.reply_text(msg, parse_mode='Markdown')