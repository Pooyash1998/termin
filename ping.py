import requests

URL_TERMIN_BOT = 'https://termin-y78y.onrender.com'

def ping():
    r1 = requests.get(URL_TERMIN_BOT) 
    print(f"Ping results for {URL_TERMIN_BOT}:")
    print(f"Aachen Termin Bot: {r1.status_code}")

if __name__ == '__main__':
    ping()  