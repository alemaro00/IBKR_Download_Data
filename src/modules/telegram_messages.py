import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Preleva le variabili in modo sicuro
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Helper per formattare e inviare i report automatici (usato dal ciclo di monitoraggio)
async def send_async_portfolio_update(bot, positions, orders, pnl):
    """Invia il report automatico pianificato."""
    msg = "📊 *Aggiornamento Portafoglio Automatico*\n\n"
    msg += format_portfolio_data(positions, orders, pnl)
    # Usiamo la variabile recuperata dal file .env
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode='Markdown')

# Funzione di utilità condivisa per formattare i dati di IBKR
def format_portfolio_data(positions, orders, pnl) -> str:
    msg = "💼 *Posizioni Correnti:*\n"
    if positions:
        for pos in positions:
            msg += f"• {pos.contract.symbol}: {pos.position} @ ${pos.avgCost:.2f}\n"
    else:
        msg += "Nessuna posizione aperta.\n"
        
    msg += f"\n📝 *Ordini Aperti:* {len(orders)}\n"
    if orders:
        for trade in orders:
            msg += f"• {trade.contract.symbol}: {trade.order.action} {trade.order.totalQuantity}\n"
    else:
        msg += "Nessun ordine in sospeso.\n"
        
    msg += "\n💰 *Profitto & Perdita (P&L):*\n"
    if pnl:
        unrealized = pnl.unrealizedPnL if pnl.unrealizedPnL is not None else 0.0
        realized = pnl.realizedPnL if pnl.realizedPnL is not None else 0.0
        msg += f"Non Realizzato: ${unrealized:.2f}\nRealizzato: ${realized:.2f}\n"
    else:
        msg += "Dati P&L non disponibili.\n"
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
    account = ib.managedAccounts()[0]
    pnl = ib.pnl(account) # Accede ai dati pnl correnti registrati dall'istanza
    
    msg = "💰 *P&L Attuale:*\n"
    if pnl:
        unrealized = pnl[-1].unrealizedPnL if pnl and pnl[-1].unrealizedPnL is not None else 0.0
        realized = pnl[-1].realizedPnL if pnl and pnl[-1].realizedPnL is not None else 0.0
        msg += f"Non Realizzato: ${unrealized:.2f}\nRealizzato: ${realized:.2f}"
    else:
        msg += "Dati P&L temporaneamente non disponibili."
    await update.message.reply_text(msg, parse_mode='Markdown')

async def tutto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Risponde al comando /tutto richiedendo l'intero pacchetto informativo."""
    ib = context.bot_data['ib_instance']
    account = ib.managedAccounts()[0]
    
    # Prende tutti i dati istantaneamente
    positions = ib.positions()
    orders = ib.openTrades()
    # reqPnL è già attivo, leggiamo la lista dei pnl correnti
    pnl_list = ib.pnl(account)
    pnl = pnl_list[-1] if pnl_list else None
    
    msg = "📊 *Report Portafoglio Istantaneo*\n\n" + format_portfolio_data(positions, orders, pnl)
    await update.message.reply_text(msg, parse_mode='Markdown')