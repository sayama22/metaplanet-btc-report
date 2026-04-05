"""
Step 1: データ収集スクリプト
- Bitcoin価格 (CoinGecko API - 無料)
- メタプラネット株価 3350.T (yfinance - 無料)
- メタプラネット関連ニュース (Google News RSS - 無料)
- 収集データ → Google Sheets に保存
- 収集データ → data.json に保存 (次のステップで参照)
"""

import os
import json
import requests
import yfinance as yf
import feedparser
from datetime import datetime, timezone, timedelta
from google.oauth2.service_account import Credentials
import gspread

JST = timezone(timedelta(hours=9))


def get_bitcoin_price() -> dict:
    """CoinGecko APIでBTC価格を取得（無料・APIキー不要）"""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd,jpy",
        "include_24hr_change": "true",
        "include_market_cap": "true",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()["bitcoin"]
    return {
        "usd": data["usd"],
        "jpy": data["jpy"],
        "change_24h_pct": round(data.get("usd_24h_change", 0), 2),
        "market_cap_usd": data.get("usd_market_cap", 0),
    }


def get_metaplanet_stock() -> dict:
    """yfinanceでメタプラネット(3350.T)の株価を取得"""
    ticker = yf.Ticker("3350.T")
    hist = ticker.history(period="5d")  # 5営業日分取得
    if hist.empty:
        return {"error": "株価データを取得できませんでした"}

    latest = hist.iloc[-1]
    prev = hist.iloc[-2] if len(hist) >= 2 else latest
    change_pct = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100

    return {
        "price": round(float(latest["Close"]), 1),
        "open": round(float(latest["Open"]), 1),
        "high": round(float(latest["High"]), 1),
        "low": round(float(latest["Low"]), 1),
        "volume": int(latest["Volume"]),
        "change_pct": round(change_pct, 2),
        "prev_close": round(float(prev["Close"]), 1),
    }


def get_metaplanet_news(limit: int = 5) -> list:
    """Google News RSSでメタプラネット関連ニュースを取得"""
    url = "https://news.google.com/rss/search"
    params = "q=メタプラネット+ビットコイン&hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(f"{url}?{params}")

    news = []
    for entry in feed.entries[:limit]:
        news.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "source": entry.get("source", {}).get("title", ""),
        })
    return news


def save_to_google_sheets(data: dict) -> None:
    """Google Sheetsにデータを追記保存"""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")

    if not creds_json or not spreadsheet_id:
        print("[SKIP] Google Sheets: 環境変数が未設定のためスキップします")
        return

    creds_dict = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)

    # --- 価格データシート ---
    try:
        ws = sh.worksheet("価格データ")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="価格データ", rows=10000, cols=20)
        ws.append_row([
            "日時(JST)", "BTC_USD", "BTC_JPY", "BTC_24h変化率(%)",
            "META_終値(円)", "META_始値", "META_高値", "META_安値",
            "META_出来高", "META_前日比(%)"
        ])

    btc = data["bitcoin"]
    stock = data["metaplanet_stock"]
    ws.append_row([
        data["timestamp"],
        btc.get("usd", ""), btc.get("jpy", ""), btc.get("change_24h_pct", ""),
        stock.get("price", ""), stock.get("open", ""),
        stock.get("high", ""), stock.get("low", ""),
        stock.get("volume", ""), stock.get("change_pct", ""),
    ])

    # --- ニュースシート ---
    try:
        news_ws = sh.worksheet("ニュース")
    except gspread.WorksheetNotFound:
        news_ws = sh.add_worksheet(title="ニュース", rows=10000, cols=10)
        news_ws.append_row(["日時(JST)", "タイトル", "URL", "ソース", "公開日"])

    for article in data["metaplanet_news"]:
        news_ws.append_row([
            data["timestamp"],
            article.get("title", ""),
            article.get("link", ""),
            article.get("source", ""),
            article.get("published", ""),
        ])

    print(f"[OK] Google Sheetsにデータを保存しました: {data['timestamp']}")


def main():
    now = datetime.now(JST)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S JST")
    date_str = now.strftime("%Y-%m-%d")

    print(f"=== データ収集開始: {timestamp} ===")

    print("📡 Bitcoin価格を取得中...")
    btc = get_bitcoin_price()
    print(f"  BTC: ${btc['usd']:,} USD / ¥{btc['jpy']:,} JPY  (24h: {btc['change_24h_pct']:+.2f}%)")

    print("📡 メタプラネット株価を取得中...")
    stock = get_metaplanet_stock()
    if "error" not in stock:
        print(f"  3350.T: ¥{stock['price']:,}  ({stock['change_pct']:+.2f}%)")
    else:
        print(f"  [WARN] {stock['error']}")

    print("📡 ニュースを取得中...")
    news = get_metaplanet_news()
    print(f"  {len(news)}件のニュースを取得しました")

    data = {
        "timestamp": timestamp,
        "date": date_str,
        "bitcoin": btc,
        "metaplanet_stock": stock,
        "metaplanet_news": news,
    }

    # JSON保存（次ステップのHTMLレポート生成で使用）
    os.makedirs("output", exist_ok=True)
    with open("output/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("[OK] output/data.json を保存しました")

    # Google Sheetsに保存
    save_to_google_sheets(data)

    print("=== データ収集完了 ===")


if __name__ == "__main__":
    main()
