from typing import Final
import requests
import telegram
import os
from flask import Flask
from flask_apscheduler import APScheduler
from termin import superc_termin


BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

CHANNEL_ID: Final = '@aachen_termin'
APPOINTMENT_LINK = 'https://termine.staedteregion-aachen.de/auslaenderamt/rsvchange?id=d5e73a2c-6e36-449b-b238-95819ba45b82'
URL: Final = 'https://termin-y78y.onrender.com'

@app.route('/status')
def status():    
    return 'OK'

@app.route('/')
def hello_world():    
    return 'Hello, World!'

@scheduler.task('interval', id='do_job_1', seconds=60, misfire_grace_time=900)
def job1():    
    bot = telegram.Bot(token=BOT_TOKEN)
    notify_aachen_termin(bot)


def notify_aachen_termin(bot: telegram.Bot):
    for pos in [0]:
        is_available, res = superc_termin(pos)
        if is_available:            
            text = f"{res}\n[🔥 Book Now\!]({APPOINTMENT_LINK})"
            text = text.replace(".", "\.")
            bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode='MarkdownV2')
    
@scheduler.task('interval', id='do_job_2', seconds=300, misfire_grace_time=900)
def job2():
    r = requests.get(f'{URL}/status')
    print(r)