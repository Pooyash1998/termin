from flask import Flask
import requests
import threading
import time
import os
from termin import superc_termin  # or whatever module name your logic is in

# === Read Telegram settings from environment ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

app = Flask(__name__)
# === Telegram Send ===
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

# === Appointment Check Loop ===
def appointment_loop():
    while True:
        success, result = superc_termin()
        if success:
            result += '\n\n<a href="https://termine.staedteregion-aachen.de/auslaenderamt/rsvchange?id=d5e73a2c-6e36-449b-b238-95819ba45b82">🔗 Change the Termin</a>'  
        else:
            result = "No appointments available."
        send_telegram_message(result)
        time.sleep(30)

# === HTTP Endpoint (keeps Render alive) ===
@app.route("/")
def home():
    return "Service is running."

# === Launch everything ===
if __name__ == "__main__":
    # Start background loop in a separate thread
    t = threading.Thread(target=appointment_loop, daemon=True)
    t.start()

    # Start Flask app
    app.run(host="0.0.0.0", port=10000)
    send_telegram_message("Test message from appointment bot")