import os
import requests
import pandas as pd
import ta

# Telegram Ayarları (GitHub Secrets üzerinden alınır)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram token veya Chat ID tanımlanmamış!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram mesajı gönderilemedi: {e}")

def get_binance_usdt_pairs():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    res = requests.get(url).json()
    pairs = [
        item['symbol'] for item in res 
        if item['symbol'].endswith('USDT') and not item['symbol'].endswith('UPUSDT') and not item['symbol'].endswith('DOWNUSDT')
    ]
    return pairs

def check_rsi():
    symbols = get_binance_usdt_pairs()
    alerts = []
    
    print(f"Toplam {len(symbols)} USDT çifti taranıyor...")
    
    for symbol in symbols:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=30m&limit=100"
            data = requests.get(url).json()
            if not isinstance(data, list) or len(data) < 30:
                continue
                
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'
            ])
            df['close'] = df['close'].astype(float)
            
            # RSI (14) Hesaplama
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            last_rsi = df['rsi'].iloc[-1]
            last_price = df['close'].iloc[-1]
            
            # Aşırı Satım (Aşırı Dip) -> RSI <= 30
            if last_rsi <= 30:
                alerts.append(f"🟢 *AŞIRI SATIM (DİP)*\n• *Coin:* #{symbol}\n• *Fiyat:* {last_price}\n• *RSI (30dk):* {last_rsi:.2f}\n")
            # Aşırı Alım (Aşırı Tepe) -> RSI >= 70
            elif last_rsi >= 70:
                alerts.append(f"🔴 *AŞIRI ALIM (TEPE)*\n• *Coin:* #{symbol}\n• *Fiyat:* {last_price}\n• *RSI (30dk):* {last_rsi:.2f}\n")
        except Exception:
            continue

    if alerts:
        message = "📊 *30 DAKİKALIK RSI SİNYALLERİ*\n\n" + "\n---\n".join(alerts)
        if len(message) > 4000:
            for i in range(0, len(message), 4000):
                send_telegram_message(message[i:i+4000])
        else:
            send_telegram_message(message)
        print("Sinyaller Telegram'a gönderildi.")
    else:
        print("Şu anda RSI <= 30 veya >= 70 olan coin bulunamadı.")

if __name__ == "__main__":
    check_rsi()
