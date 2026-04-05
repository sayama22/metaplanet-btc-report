# 📊 メタプラネット × BTC デイリーレポート 自動化システム

GitHub Actions で毎日自動的にメタプラネット(3350.T)とBitcoinのデータを収集し、
Tailwind CSS製HTMLレポートを生成・公開・LINE通知するシステムです。

## 🏗️ システム全体像

```
GitHub Actions (毎日 JST 10:00)
  │
  ├─ Job 1: データ収集
  │    ├─ BTC価格 (CoinGecko API)
  │    ├─ メタプラネット株価 (yfinance)
  │    ├─ ニュース (Google News RSS)
  │    └─ → Google Sheets に保存
  │
  ├─ Job 2: HTMLレポート生成
  │    └─ Tailwind CSS + Chart.js で可視化
  │
  ├─ Job 3: AIサブエージェント レビュー
  │    └─ Gemini 1.5 Flash でレポートを解説
  │
  ├─ Job 4: Surge にデプロイ (公開URL)
  │
  └─ Job 5: LINE通知 (公式アカウントから送信)
```

## 💰 無料枠での運用コスト

| サービス | 無料枠 | 使用量/日 |
|---|---|---|
| GitHub Actions | パブリックRepo: 無制限 | ~2分/日 |
| CoinGecko API | 10,000回/月 | 1回/日 |
| yfinance | 無制限（非公式） | 1回/日 |
| Google Sheets API | 300リクエスト/分 | 数回/日 |
| Gemini 1.5 Flash | 1,500回/日 | 1回/日 |
| Surge.sh | 無制限（公開サブドメイン） | 1デプロイ/日 |
| LINE Messaging API | 200通/月 | 1通/日 |

---

## ⚙️ セットアップ手順

### Step 1: GitHubリポジトリを作成

```bash
# このフォルダをGitリポジトリにする
git init
git add .
git commit -m "initial commit"

# GitHubでリポジトリを作成（パブリック推奨）
# https://github.com/new

git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git push -u origin main
```

> ⚠️ **パブリックリポジトリ推奨**: GitHub Actions の無料枠が無制限になります

---

### Step 2: Google Sheets + サービスアカウント 設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」→ **Google Sheets API** を有効化
4. 「APIとサービス」→「認証情報」→「サービスアカウントを作成」
   - 名前: `github-actions-sheets`
   - ロール: 「編集者」
5. サービスアカウントのメールアドレスをコピー
6. 「鍵を追加」→「新しい鍵を作成」→ **JSON** を選択してダウンロード
7. [Google Sheets](https://sheets.google.com) で新しいスプレッドシートを作成
8. スプレッドシートをサービスアカウントのメールと**共有**（編集者権限）
9. URLからスプレッドシートIDをコピー:
   `https://docs.google.com/spreadsheets/d/【ここがID】/edit`

---

### Step 3: Gemini API キー取得

1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. 「APIキーを作成」→ キーをコピー
3. 無料枠: Gemini 1.5 Flash = 15リクエスト/分、1,500回/日

---

### Step 4: Surge アカウント・トークン取得

```bash
# Surgeをインストール（初回のみ）
npm install -g surge

# アカウント作成 & トークン取得
surge token
# → 表示されたトークンをコピー
```

デプロイ先のサブドメインを決める:
- 例: `metaplanet-btc-report.surge.sh`
- 他の人が使っていなければ自由に設定可能

---

### Step 5: LINE Messaging API 設定

1. [LINE Developers](https://developers.line.biz/) にアクセス
2. プロバイダーを作成 → 「Messaging API」チャンネルを作成
3. 「Messaging API設定」→ **チャンネルアクセストークン（長期）** を発行してコピー
4. 「基本設定」→ **あなたのUser ID** をコピー
   （または友達追加後、Webhookで取得）

> 💡 **無料プランの注意**: 月200通まで。毎日送るなら月約30通なので余裕です。

---

### Step 6: GitHub Secrets に登録

リポジトリの Settings → Secrets and variables → Actions → New repository secret

| Secret名 | 内容 | 取得場所 |
|---|---|---|
| `GOOGLE_CREDENTIALS_JSON` | サービスアカウントJSONの**全内容**をペースト | Step 2でダウンロードしたJSONファイル |
| `SPREADSHEET_ID` | スプレッドシートのID | Step 2でコピーしたID |
| `GEMINI_API_KEY` | Gemini APIキー | Step 3 |
| `SURGE_TOKEN` | SurgeのTokenトークン | Step 4 |
| `SURGE_DOMAIN` | デプロイ先ドメイン | 例: `metaplanet-btc-report.surge.sh` |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINEチャンネルアクセストークン | Step 5 |
| `LINE_USER_ID` | LINE ユーザーID | Step 5 |

---

### Step 7: 動作確認（手動実行）

1. GitHubリポジトリの「Actions」タブを開く
2. 「📊 メタプラネット×BTC デイリーレポート」を選択
3. 「Run workflow」→「Run workflow」をクリック
4. 各Jobが順番に実行されることを確認

---

## 📁 ファイル構成

```
課題3/
├── .github/
│   └── workflows/
│       └── daily-report.yml      # GitHub Actionsワークフロー
├── scripts/
│   ├── 1_collect_data.py         # データ収集 → Google Sheets
│   ├── 2_generate_report.py      # HTMLレポート生成
│   ├── 3_review_report.py        # AIサブエージェントレビュー
│   └── 4_notify_line.py          # LINE通知
├── output/                       # 生成物の保存先（Git管理外）
│   ├── data.json                 # 収集データ
│   ├── index.html                # 生成レポート
│   └── review.txt                # AIレビューテキスト
├── requirements.txt              # Python依存関係
└── README.md                     # このファイル
```

---

## 🔧 トラブルシューティング

### メタプラネット株価が取得できない
- 東証の取引時間外（9:00〜15:30 JST）のため前日のデータが表示されます
- 土日祝は株式市場が休みのため前営業日のデータになります

### Google Sheetsへの書き込みに失敗する
- サービスアカウントにスプレッドシートを共有しているか確認
- `GOOGLE_CREDENTIALS_JSON` が正しくJSON全体を貼り付けているか確認

### Surge デプロイに失敗する
- `SURGE_TOKEN` が正しいか確認: `surge token` で再取得
- ドメインが他のSurgeユーザーに使われていないか確認

### LINE通知が届かない
- LINE Official Account Managerでwebhookが無効になっていないか確認
- `LINE_USER_ID` はあなた自身のUserIDか確認（チャンネルIDではない）

---

## ⏰ スケジュール変更

`daily-report.yml` の cron を変更:

```yaml
schedule:
  - cron: '0 1 * * *'   # JST 10:00 (UTC 01:00)
  # 変更例:
  # - cron: '0 0 * * *'   # JST 09:00
  # - cron: '30 0 * * *'  # JST 09:30
  # - cron: '0 1 * * 1-5' # 平日のみ JST 10:00
```
