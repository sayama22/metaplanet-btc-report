"""
Step 4: LINE通知スクリプト
- SurgeにデプロイされたURLをLINE公式アカウントから送信
- LINE Messaging API (無料枠: 月200通)
- 環境変数: LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID
"""

import os
import json
import requests


def load_data() -> dict:
    with open("output/data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_line_message(data: dict, surge_url: str) -> dict:
    btc = data["bitcoin"]
    stock = data.get("metaplanet_stock", {})
    date_str = data.get("date", "")

    btc_change = btc.get("change_24h_pct", 0)
    meta_change = stock.get("change_pct", 0)

    btc_emoji = "📈" if float(btc_change or 0) >= 0 else "📉"
    meta_emoji = "📈" if float(meta_change or 0) >= 0 else "📉"
    btc_sign = "+" if float(btc_change or 0) >= 0 else ""
    meta_sign = "+" if float(meta_change or 0) >= 0 else ""

    text = (
        f"📊 メタプラネット×BTCデイリーレポート\n"
        f"📅 {date_str}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"₿ BTC: ${float(btc.get('usd', 0)):,.0f}\n"
        f"   ¥{float(btc.get('jpy', 0)):,.0f} ({btc_emoji}{btc_sign}{btc_change:.2f}%)\n"
        f"\n"
        f"🏢 メタプラネット(3350.T)\n"
        f"   ¥{stock.get('price', 'N/A')} ({meta_emoji}{meta_sign}{float(meta_change or 0):.2f}%)\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📋 詳細レポート:\n{surge_url}"
    )

    return {
        "to": os.environ.get("LINE_USER_ID", ""),
        "messages": [
            {
                "type": "text",
                "text": text,
            }
        ],
    }


def send_line_message(payload: dict) -> None:
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        print("[SKIP] LINE_CHANNEL_ACCESS_TOKEN が未設定のためスキップします")
        return
    if not payload.get("to"):
        print("[SKIP] LINE_USER_ID が未設定のためスキップします")
        return

    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        data=json.dumps(payload),
        timeout=30,
    )

    if resp.status_code == 200:
        print("[OK] LINEに通知を送信しました")
    else:
        print(f"[ERROR] LINE通知に失敗: {resp.status_code} {resp.text}")
        raise RuntimeError(f"LINE API error: {resp.status_code}")


def main():
    surge_domain = os.environ.get("SURGE_DOMAIN", "metaplanet-btc-report.surge.sh")
    surge_url = f"https://{surge_domain}"

    print(f"=== LINE通知送信開始 ===")
    print(f"  Surge URL: {surge_url}")

    data = load_data()
    payload = build_line_message(data, surge_url)
    send_line_message(payload)

    print("=== LINE通知送信完了 ===")


if __name__ == "__main__":
    main()
