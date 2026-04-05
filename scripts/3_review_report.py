"""
Step 3: AIサブエージェント レビュースクリプト（親エージェントの部下）
- Google Gemini 1.5 Flash API (無料枠: 15 RPM / 1M tokens/day)
- output/index.html + output/data.json を読み込み
- Gemini にレポート品質・市場コメントをレビューさせる
- レビュー結果をHTMLのプレースホルダーに埋め込む
"""

import os
import json
import google.generativeai as genai

PLACEHOLDER = "<!-- AI_REVIEW_PLACEHOLDER -->"


def load_data() -> dict:
    with open("output/data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_html() -> str:
    with open("output/index.html", "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(data: dict) -> str:
    btc = data["bitcoin"]
    stock = data.get("metaplanet_stock", {})
    news = data.get("metaplanet_news", [])
    news_titles = "\n".join(f"- {n['title']}" for n in news)

    return f"""あなたは金融・暗号資産アナリストのAIサブエージェントです。
親エージェントが生成した本日のメタプラネット×BTCレポートをレビューしてください。

【本日のデータ】
- BTC価格: ${btc.get('usd', 'N/A'):,} USD / ¥{btc.get('jpy', 'N/A'):,} JPY
- BTC 24h変化率: {btc.get('change_24h_pct', 'N/A')}%
- メタプラネット(3350.T) 終値: ¥{stock.get('price', 'N/A')}
- メタプラネット 前日比: {stock.get('change_pct', 'N/A')}%
- 高値: ¥{stock.get('high', 'N/A')} / 安値: ¥{stock.get('low', 'N/A')}

【本日のニュース見出し】
{news_titles if news_titles else '（ニュースなし）'}

以下の形式で日本語でレビューを作成してください：
1. **市場サマリー**（2〜3文）: 本日の全体的な市場状況
2. **注目ポイント**（箇条書き2〜3項目）: 投資家が注目すべき点
3. **リスク・留意事項**（1〜2文）: 注意すべきリスク
4. **明日の展望**（1〜2文）: 翌日の見通し

※ 投資推奨は行わず、あくまで情報提供として記述してください。
※ 簡潔かつ読みやすい日本語でお願いします。"""


def render_review_html(review_text: str) -> str:
    """Geminiのテキスト回答をHTMLに変換"""
    lines = review_text.strip().split("\n")
    html_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("**") and line.endswith("**"):
            text = line.strip("**")
            html_parts.append(
                f'<h3 class="text-indigo-300 font-semibold mt-4 mb-1">{text}</h3>'
            )
        elif line.startswith("**") and "**" in line[2:]:
            # **タイトル**: 内容 形式
            bold_end = line.index("**", 2)
            title = line[2:bold_end]
            rest = line[bold_end + 2:].strip().lstrip(":").strip()
            html_parts.append(
                f'<h3 class="text-indigo-300 font-semibold mt-4 mb-1">{title}</h3>'
            )
            if rest:
                html_parts.append(f'<p class="text-gray-300 text-sm leading-relaxed">{rest}</p>')
        elif line.startswith("- ") or line.startswith("• "):
            content = line[2:].strip()
            html_parts.append(
                f'<li class="flex items-start gap-2 text-gray-300 text-sm">'
                f'<span class="text-indigo-400 mt-0.5">◆</span>{content}</li>'
            )
        elif line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4."):
            html_parts.append(
                f'<p class="text-gray-300 text-sm leading-relaxed mt-2">{line}</p>'
            )
        else:
            html_parts.append(
                f'<p class="text-gray-300 text-sm leading-relaxed">{line}</p>'
            )

    content_html = "\n".join(html_parts)
    return f"""
<div class="prose prose-invert max-w-none">
  <ul class="space-y-1 list-none pl-0">
    {content_html}
  </ul>
  <p class="text-xs text-gray-600 mt-4 pt-3 border-t border-gray-700">
    ※ このレビューはGemini 1.5 Flash（AI）が自動生成したものです。投資判断の根拠とすることはお控えください。
  </p>
</div>"""


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[SKIP] GEMINI_API_KEY が未設定のため、AIレビューをスキップします")
        # プレースホルダーをスキップメッセージに置き換え
        html = load_html()
        skip_html = """
<div class="text-gray-500 text-sm">
  <p>⚠️ AIレビューはスキップされました（GEMINI_API_KEY が未設定）</p>
</div>"""
        html = html.replace(PLACEHOLDER, skip_html)
        with open("output/index.html", "w", encoding="utf-8") as f:
            f.write(html)
        return

    print("=== AIサブエージェント レビュー開始 ===")

    genai.configure(api_key=api_key)

    # Gemini 1.5 Flash (無料枠)
    model = genai.GenerativeModel("gemini-1.5-flash")

    data = load_data()
    prompt = build_prompt(data)

    print("🤖 Geminiにレビューを依頼中...")
    response = model.generate_content(prompt)
    review_text = response.text
    print(f"[OK] レビュー取得完了 ({len(review_text)}文字)")

    # レビュー結果をHTMLに埋め込む
    review_html = render_review_html(review_text)
    html = load_html()
    html = html.replace(PLACEHOLDER, review_html)

    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    # レビュー本文も保存（デバッグ用）
    with open("output/review.txt", "w", encoding="utf-8") as f:
        f.write(review_text)

    print("[OK] output/index.html にAIレビューを埋め込みました")
    print("=== AIサブエージェント レビュー完了 ===")


if __name__ == "__main__":
    main()
