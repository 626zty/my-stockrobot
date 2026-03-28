import pandas as pd
import requests
import yfinance as yf
from FinMind.data import DataLoader

api = DataLoader()
api.login_by_token(api_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMy0yOCAxMzozMjozOCIsInVzZXJfaWQiOiJ6dHk2MjYiLCJlbWFpbCI6Inp0eTkzMDYyNkBnbWFpbC5jb20iLCJpcCI6IjM2LjIzOC45NC4yMjcifQ.vDsDHoiX11SFAH3wLZ-UbyjpwIW5FBh4oMG0o1On2-s")

watch_list = {
    "2330": "台積電", "2454": "聯發科", 
    "3443": "創意", "3661": "世芯-KY", 
    "2317": "鴻海", "2382": "廣達", 
    "2881": "富邦金", "2891": "中信金", "2882": "國泰金",
    "0050": "元大台灣50", "0056": "元大高股息"
}

vix_data = yf.download("^VIX", period="5d")
vix_close = float(vix_data['Close'].iloc[-1])

tsm_data = yf.download("TSM", period="5d")
adr_price = float(tsm_data['Close'].iloc[-1])

exchange_data = yf.download("TWD=X", period="5d")
usd_to_twd = float(exchange_data['Close'].iloc[-1])

report_lines = []
report_lines.append("📊 **【盤前自動化沙盤推演】** 📊")
report_lines.append(f"🌡️ **大盤溫度計** | VIX 恐慌指數: `{vix_close:.2f}`")
report_lines.append("-" * 30)

for stock_id, name in watch_list.items():
    try:
        stock_price = api.taiwan_stock_daily(stock_id=stock_id, start_date="2025-03-20")
        current_close = float(stock_price['close'].iloc[-1])
        prev_close = float(stock_price['close'].iloc[-2])
        price_change = ((current_close - prev_close) / prev_close) * 100

        inst_data = api.taiwan_stock_institutional_investors(stock_id=stock_id, start_date="2025-03-20")
        foreign = inst_data[inst_data['name'] == 'Foreign_Investor']
        net_buy = 0
        if not foreign.empty:
            net_buy = (float(foreign['buy'].iloc[-1]) - float(foreign['sell'].iloc[-1])) / 1000 

        signal = "平穩"
        if price_change < -2 and net_buy > 1000:
            signal = "🚨 異常低接：股價重挫但外資大買"
        elif price_change > 2 and net_buy < -1000:
            signal = "⚠️ 異常倒貨：股價大漲但外資大賣"
        
        if stock_id == "2330":
            equivalent_price = (adr_price * usd_to_twd) / 5
            premium = ((equivalent_price - current_close) / current_close) * 100
            signal += f" | ADR溢價: {premium:.2f}%"

        report_lines.append(f"🔹 **{name} ({stock_id})** | 昨收: {current_close} ({price_change:+.1f}%) | 外資: {net_buy:+.0f}張 | {signal}")
    except Exception as e:
        continue

webhook_url = "https://discord.com/api/webhooks/1487329548272926782/dxRe5L4pLNOzD1-M9ReoabiktnqHMHiXHqF-fKXp5O-2LHA3Dp95OZs6wU9rq5MpA5mU"
payload = {
    "username": "半導體沙盤機器人",
    "content": "\n".join(report_lines)
}
requests.post(webhook_url, json=payload)
print("✅ 報告已送出！")