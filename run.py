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
        print("Telegram config missing", flush=True)
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, data=payload)
        print(f"Telegram send status: {res.status_code} - {res.text}", flush=True)
        return res.ok
    except Exception as e:
        print(f"Error sending message: {e}", flush=True)
        return False

def appointment_loop():
    last_message = None
    while True:
        try:
            success, result = superc_termin()
            if success:
                result += '\n\n<a href="https://termine.staedteregion-aachen.de/auslaenderamt/rsvchange?id=d5e73a2c-6e36-449b-b238-95819ba45b82">🔗 Change the Termin</a>'
                if result != last_message:
                    sent = send_telegram_message(result)
                    if sent:
                        print("Sent new appointment message.", flush=True)
                        last_message = result
                    else:
                        print("Failed to send appointment message.", flush=True)
                else:
                    print("No new appointment updates, not sending message.", flush=True)
            else:
                print("No appointments available.", flush=True)
            time.sleep(30)
        except Exception as e:
            print(f"Error in appointment loop: {e}", flush=True)
            time.sleep(30)

started = False

@app.before_first_request
def start_background_thread():
    global started
    if not started:
        print("Starting appointment loop thread...", flush=True)
        # Send a startup message once
        send_telegram_message("Appointment bot started.")
        t = threading.Thread(target=appointment_loop, daemon=True)
        t.start()
        started = True

@app.route("/")
def home():
    return "Service is running."

# Note: No need for if __name__ == "__main__" when running under Gunicorn