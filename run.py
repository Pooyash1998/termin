from flask import Flask
import requests
import threading
import time
import os
from termin import superc_termin  # your logic here

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

app = Flask(__name__)

def send_telegram_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram config missing")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, data=payload)
        print(f"Telegram send status: {res.status_code} - {res.text}")
        return res.ok
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def appointment_loop():
    last_message = None
    while True:
        try:
            success, result = superc_termin()
            if success:
                result += '\n\n<a href="https://termine.staedteregion-aachen.de/auslaenderamt/rsvchange?id=d5e73a2c-6e36-449b-b238-95819ba45b82">🔗 Change the Termin</a>'
                if result != last_message:  # send only if changed
                    sent = send_telegram_message(result)
                    if sent:
                        print("Sent new appointment message.")
                        last_message = result
                    else:
                        print("Failed to send appointment message.")
                else:
                    print("No new appointment updates, not sending message.")
            else:
                print("No appointments available.")
                # Optional: send only once or after long intervals if needed
            time.sleep(30)
        except Exception as e:
            print(f"Error in appointment loop: {e}")
            time.sleep(30)

@app.route("/")
def home():
    return "Service is running."

if __name__ == "__main__":
    # Test Telegram on startup
    send_telegram_message("Appointment bot started.")

    # Start background thread
    t = threading.Thread(target=appointment_loop, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=10000)