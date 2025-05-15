from flask import Flask
import requests
import os
from termin import superc_termin  # or whatever module name your logic is in

# === Read Telegram settings from environment ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        return False  # Fail silently if misconfigured

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, data=payload)
        return res.ok
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

# === Flask app ===
app = Flask(__name__)

@app.route("/")
def ping():
    success, result = superc_termin()
    # Add link at the bottom
    result += '\n\n<a href="https://termine.staedteregion-aachen.de/auslaenderamt/rsvchange?id=d5e73a2c-6e36-449b-b238-95819ba45b82">🔗 Change the Termin</a>'
    send_telegram_message(result if success else "No appointments.")
    return result if success else "No appointments found."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)