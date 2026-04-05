"""
Step 2: HTMLレポート生成スクリプト
- output/data.json を読み込み
- Tailwind CSS + Chart.js を使ったレポートHTMLを生成
- output/index.html に保存
"""

import json
import os
from datetime import datetime


def load_data() -> dict:
    with open("output/data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def format_number(n, decimals=0) -> str:
    if n is None or n == "":
        return "N/A"
    try:
        return f"{float(n):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(n)


def change_color(val) -> str:
    """変化率の色クラスを返す"""
    try:
        return "text-emerald-400" if float(val) >= 0 else "text-red-400"
    except (ValueError, TypeError):
        return "text-gray-400"


def change_arrow(val) -> str:
    try:
        return "▲" if float(val) >= 0 else "▼"
    except (ValueError, TypeError):
        return "–"


def generate_html(data: dict) -> str:
    btc = data["bitcoin"]
    stock = data.get("metaplanet_stock", {})
    news = data.get("metaplanet_news", [])
    timestamp = data.get("timestamp", "")
    date_str = data.get("date", "")

    btc_usd = format_number(btc.get("usd"), 0)
    btc_jpy = format_number(btc.get("jpy"), 0)
    btc_change = btc.get("change_24h_pct", 0)
    btc_change_str = f"{change_arrow(btc_change)} {abs(float(btc_change)):.2f}%"
    btc_color = change_color(btc_change)

    meta_price = format_number(stock.get("price"), 1)
    meta_change = stock.get("change_pct", 0)
    meta_change_str = f"{change_arrow(meta_change)} {abs(float(meta_change)):.2f}%" if meta_change != "" else "N/A"
    meta_color = change_color(meta_change)
    meta_high = format_number(stock.get("high"), 1)
    meta_low = format_number(stock.get("low"), 1)
    meta_volume = format_number(stock.get("volume"), 0)

    # ニュースHTMLを構築
    news_items_html = ""
    for article in news:
        title = article.get("title", "")
        link = article.get("link", "#")
        source = article.get("source", "")
        published = article.get("published", "")
        news_items_html += f"""
        <li class="border border-gray-700 rounded-xl p-4 hover:border-indigo-500 transition-colors duration-200">
          <a href="{link}" target="_blank" rel="noopener noreferrer"
             class="text-blue-400 hover:text-blue-300 font-medium leading-snug block mb-1">
            {title}
          </a>
          <div class="flex items-center gap-3 text-xs text-gray-500 mt-1">
            <span>{source}</span>
            <span>·</span>
            <span>{published}</span>
          </div>
        </li>"""

    if not news_items_html:
        news_items_html = '<li class="text-gray-500 text-sm">ニュースが見つかりませんでした</li>'

    # AIレビュー欄のプレースホルダー（Step 3で埋め込む）
    review_placeholder = "<!-- AI_REVIEW_PLACEHOLDER -->"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>📊 メタプラネット × BTC デイリーレポート {date_str}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body {{ background: #0f1117; }}
    .card {{ background: #1a1d2e; border: 1px solid #2d3149; }}
    .gradient-text {{
      background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .glow-indigo {{ box-shadow: 0 0 24px rgba(99,102,241,0.25); }}
    .glow-orange {{ box-shadow: 0 0 24px rgba(251,146,60,0.25); }}
  </style>
</head>
<body class="min-h-screen text-white font-sans">

  <!-- Header -->
  <header class="border-b border-gray-800 px-6 py-4">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-2xl">📊</span>
        <div>
          <h1 class="text-xl font-bold gradient-text">メタプラネット × BTC デイリーレポート</h1>
          <p class="text-xs text-gray-500">自動生成 | {timestamp}</p>
        </div>
      </div>
      <div class="text-right">
        <p class="text-xs text-gray-500">Powered by</p>
        <p class="text-xs text-gray-400">GitHub Actions + Gemini AI</p>
      </div>
    </div>
  </header>

  <!-- Main -->
  <main class="max-w-6xl mx-auto px-6 py-8 space-y-8">

    <!-- KPI Cards -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-6">

      <!-- Bitcoin Card -->
      <div class="card rounded-2xl p-6 glow-orange">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">₿</span>
          <div>
            <p class="text-xs text-gray-400 uppercase tracking-widest">Bitcoin</p>
            <p class="text-sm text-gray-300">BTC / USD・JPY</p>
          </div>
        </div>
        <div class="mb-4">
          <p class="text-4xl font-bold text-orange-400">${btc_usd}</p>
          <p class="text-xl text-gray-300 mt-1">¥{btc_jpy} <span class="text-sm text-gray-500">JPY</span></p>
        </div>
        <div class="flex items-center gap-2">
          <span class="px-3 py-1 rounded-full text-sm font-semibold {btc_color} bg-gray-800">
            {btc_change_str}
          </span>
          <span class="text-xs text-gray-500">24時間変化率</span>
        </div>
      </div>

      <!-- Metaplanet Card -->
      <div class="card rounded-2xl p-6 glow-indigo">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">🏢</span>
          <div>
            <p class="text-xs text-gray-400 uppercase tracking-widest">Metaplanet</p>
            <p class="text-sm text-gray-300">3350.T / 東証スタンダード</p>
          </div>
        </div>
        <div class="mb-4">
          <p class="text-4xl font-bold text-indigo-400">¥{meta_price}</p>
          <p class="text-sm text-gray-500 mt-1">終値</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="px-3 py-1 rounded-full text-sm font-semibold {meta_color} bg-gray-800">
            {meta_change_str}
          </span>
          <span class="text-xs text-gray-500">前日比</span>
        </div>
        <!-- サブ指標 -->
        <div class="grid grid-cols-3 gap-3 mt-5 pt-4 border-t border-gray-700 text-center">
          <div>
            <p class="text-xs text-gray-500">高値</p>
            <p class="text-sm font-semibold text-gray-200">¥{meta_high}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500">安値</p>
            <p class="text-sm font-semibold text-gray-200">¥{meta_low}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500">出来高</p>
            <p class="text-sm font-semibold text-gray-200">{meta_volume}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Chart Section -->
    <section class="card rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-gray-200 mb-4">📈 本日のサマリーチャート</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <p class="text-xs text-gray-500 mb-2 text-center">BTC 24h変化率 vs META 前日比</p>
          <canvas id="changeChart" height="200"></canvas>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-2 text-center">メタプラネット 本日の値動き</p>
          <canvas id="priceRangeChart" height="200"></canvas>
        </div>
      </div>
    </section>

    <!-- News Section -->
    <section class="card rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-gray-200 mb-4">📰 最新ニュース（メタプラネット × BTC）</h2>
      <ul class="space-y-3">
        {news_items_html}
      </ul>
    </section>

    <!-- AI Review Section -->
    <section class="card rounded-2xl p-6 border-indigo-800" id="ai-review">
      <div class="flex items-center gap-2 mb-4">
        <span class="text-lg">🤖</span>
        <h2 class="text-lg font-semibold text-gray-200">AI サブエージェント レビュー</h2>
        <span class="px-2 py-0.5 text-xs rounded-full bg-indigo-900 text-indigo-300">Gemini 1.5 Flash</span>
      </div>
      {review_placeholder}
    </section>

  </main>

  <!-- Footer -->
  <footer class="border-t border-gray-800 px-6 py-4 mt-12">
    <div class="max-w-6xl mx-auto text-center text-xs text-gray-600">
      <p>このレポートはGitHub Actionsにより自動生成されています。投資判断の根拠とすることはお控えください。</p>
      <p class="mt-1">Generated: {timestamp} | Data: CoinGecko API, Yahoo Finance (yfinance), Google News RSS</p>
    </div>
  </footer>

  <script>
    // --- 変化率比較チャート ---
    const btcChange = {btc_change};
    const metaChange = {meta_change if meta_change != "" else 0};

    new Chart(document.getElementById('changeChart'), {{
      type: 'bar',
      data: {{
        labels: ['BTC (24h)', 'META (前日比)'],
        datasets: [{{
          label: '変化率 (%)',
          data: [btcChange, metaChange],
          backgroundColor: [
            btcChange >= 0 ? 'rgba(251,146,60,0.7)' : 'rgba(239,68,68,0.7)',
            metaChange >= 0 ? 'rgba(99,102,241,0.7)' : 'rgba(239,68,68,0.7)',
          ],
          borderColor: [
            btcChange >= 0 ? 'rgb(251,146,60)' : 'rgb(239,68,68)',
            metaChange >= 0 ? 'rgb(99,102,241)' : 'rgb(239,68,68)',
          ],
          borderWidth: 2,
          borderRadius: 8,
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f2937' }} }},
          y: {{ ticks: {{ color: '#9ca3af', callback: v => v + '%' }}, grid: {{ color: '#1f2937' }} }},
        }}
      }}
    }});

    // --- 値動きレンジチャート（高値・安値・終値） ---
    const open = {stock.get('open', 0) or 0};
    const high = {stock.get('high', 0) or 0};
    const low  = {stock.get('low',  0) or 0};
    const close = {stock.get('price', 0) or 0};

    new Chart(document.getElementById('priceRangeChart'), {{
      type: 'bar',
      data: {{
        labels: ['始値', '高値', '安値', '終値'],
        datasets: [{{
          label: '株価 (円)',
          data: [open, high, low, close],
          backgroundColor: [
            'rgba(156,163,175,0.7)',
            'rgba(52,211,153,0.7)',
            'rgba(239,68,68,0.7)',
            close >= open ? 'rgba(52,211,153,0.7)' : 'rgba(239,68,68,0.7)',
          ],
          borderRadius: 8,
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f2937' }} }},
          y: {{
            ticks: {{ color: '#9ca3af', callback: v => '¥' + v.toLocaleString() }},
            grid: {{ color: '#1f2937' }},
            min: Math.max(0, low * 0.98),
          }}
        }}
      }}
    }});
  </script>
</body>
</html>
"""
    return html


def main():
    print("=== HTMLレポート生成開始 ===")
    data = load_data()
    html = generate_html(data)

    os.makedirs("output", exist_ok=True)
    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("[OK] output/index.html を生成しました")
    print("=== HTMLレポート生成完了 ===")


if __name__ == "__main__":
    main()
