
import requests

# Inserisci qui il tuo token e chat_id
TELEGRAM_BOT_TOKEN = 'INSERISCI_IL_TUO_TOKEN'
TELEGRAM_CHAT_ID = 'INSERISCI_LA_TUA_CHAT_ID'

def send_telegram_message(message, token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID):
	"""Invia un messaggio Telegram al bot specificato."""
	url = f"https://api.telegram.org/bot{token}/sendMessage"
	data = {
		'chat_id': chat_id,
		'text': message
	}
	try:
		response = requests.post(url, data=data)
		response.raise_for_status()
	except Exception as e:
		print(f"Errore invio messaggio Telegram: {e}")


