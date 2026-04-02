import pandas as pd
import requests
import yfinance as yf
from FinMind.data import DataLoader
from datetime import datetime
import pytz

# --- 核心設定區 ---
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMy0yOCAxMzozMjozOCIsInVzZXJfaWQiOiJ6dHk2MjYiLCJlbWFpbCI6Inp0eTkzMDYyNkBnbWFpbC5jb20iLCJpcCI6IjM2LjIzOC45NC4yMjcifQ.vDsDHoiX11SFAH3wLZ-UbyjpwIW5FBh4oMG0o1On2-s"
WEBHOOK_URL = "https://discord.com/api/webhooks/1487329548272926782/dxRe5L4pLNOzD1-M9ReoabiktnqHMHiXHqF-fKXp5O-2LHA3Dp95OZs6wU9rq5MpA5mU"

WATCH_LIST = {
    "2330": "台積電", "2454": "聯發科", 
    "3443": "創意", "3661": "世芯-KY", 
    "2317": "鴻海", "2344": "華邦電", 
    "2881": "富邦金", "2891": "中信金", "2882": "國泰金",
    "0050": "元大台灣50", "0056": "元大高股息"
}

# --- 功能模組 ---

def get_pre_market_report():
    """ 總經與籌碼報告 """
    api = DataLoader()
    api.login_by_token(api_token=API_TOKEN)
    
    # 總經指標
    try:
        vix = yf.download("^VIX", period="1d", progress=False)['Close'].iloc[-1]
        adr = yf.download("TSM", period="1d", progress=False)['Close'].iloc[-1]
        usd_twd = yf.download("TWD=X", period="1d", progress=False)['Close'].iloc[-1]
        
        # 處理 yfinance 可能回傳 Series 的問題
        vix = float(vix.iloc[0]) if isinstance(vix, pd.Series) else float(vix)
        adr = float(adr.iloc[0]) if isinstance(adr, pd.Series) else float(adr)
        usd_twd = float(usd_twd.iloc[0]) if isinstance(usd_twd, pd.Series) else float(usd_twd)
    except:
        vix, adr, usd_twd = 0, 0, 32.0 # 備用值

    report = [f"☀️ **【盤前戰略地圖】** {datetime.now().strftime('%Y-%m-%d')}", f"🌡️ VIX 指數: `{vix:.2f}` | ADR 數據更新中..."]
    
    for stock_id, name in WATCH_LIST.items():
        try:
            df = api.taiwan_stock_daily(stock_id=stock_id, start_date="2025-03-20")
            close = float(df['close'].iloc[-1])
            inst = api.taiwan_stock_institutional_investors(stock_id=stock_id, start_date="2025-03-20")
            net_buy = (float(inst[inst['name'] == 'Foreign_Investor']['buy'].iloc[-1]) - 
                       float(inst[inst['name'] == 'Foreign_Investor']['sell'].iloc[-1])) / 1000
            
            msg = f"🔹 {name}: {close} 元 | 外資: {net_buy:+.0f}張"
            if stock_id == "2330":
                equivalent_price = (adr * usd_twd) / 5
                premium = ((equivalent_price - close) / close) * 100
                msg += f" | ADR 溢價: {premium:+.2f}%"
            report.append(msg)
        except: continue
    return "\n".join(report)

def get_mid_day_report():
    """ 15 分鐘微觀結構快訊 """
    report = [f"⚡ **【盤中 15min 微觀快訊】** {datetime.now().strftime('%H:%M')}"]
    
    for stock_id, name in WATCH_LIST.items():
        try:
            ticker = f"{stock_id}.TW"
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 15: continue
            
            df_15 = df.iloc[:15].copy()
            o = float(df_15['Open'].iloc[0])
            h = float(df_15['High'].max())
            l = float(df_15['Low'].min())
            c = float(df_15['Close'].iloc[-1])
            
            # 計算 VWAP
            df_15['VWAP'] = (df_15['Close'] * df_15['Volume']).cumsum() / df_15['Volume'].cumsum()
            vwap = float(df_15['VWAP'].iloc[-1])

            # 五大場景判定
            status = "🔄 震盪整理"
            if (h-l)/o < 0.015 and c > vwap: status = "🌟 蓄勢爆發"
            elif h > o and c >= o and l >= o: status = "🌊 洗盤場景"
            elif l < o and h <= o: status = "📉 偏弱場景"
            elif h > o and c < o:  status = "⚠️ 出貨信號"
            elif l < o and c > o:  status = "🚀 強勢發動"
            
            report.append(f"📍 {name}: {c} 元 ({status})")
        except: continue
    return "\n".join(report)

# --- 執行邏輯 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

# 判定要發哪份報告
if now_tw.hour == 9:
    final_message = get_mid_day_report()
else:
    # 只要不是 9 點，通通預設跑盤前報告
    final_message = get_pre_market_report()
    # 如果不是在 6, 7, 8 點發送，就加上「手動測試」字樣
    if now_tw.hour not in [6, 7, 8]:
        final_message = "🧪 **【手動測試/非準點報告】**\n" + final_message

# 發送到 Discord
if WEBHOOK_URL.startswith("http"):
    requests.post(WEBHOOK_URL, json={"username": "巴巴波以", "content": final_message})
    print(f"✅ 報告已送出 (目前台灣時間: {now_tw.strftime('%H:%M')})")