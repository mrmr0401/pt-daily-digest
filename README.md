# 📋 PT Daily Digest (理学療法士向け情報ダイジェスト)

[![PT Daily Digest Generation](https://github.com/mrmr0401/pt-daily-digest/actions/workflows/daily_digest.yml/badge.svg)](https://github.com/mrmr0401/pt-daily-digest/actions/workflows/daily_digest.yml)

理学療法士（PT）管理職のための、新着論文および医療制度情報を毎朝自動集約しスマートフォン最適化デザインで配信する完全無料のシステムです。

📱 **公開ページ (毎朝自動更新):** [https://mrmr0401.github.io/pt-daily-digest/](https://mrmr0401.github.io/pt-daily-digest/)

---

## 🌟 主な機能

- **今日のおすすめ 5選 (独自スコアリング)**: 重要キーワード一致数、最新度、被引用数（OpenAlex）から注目トピックを自動選定。
- **Gemini API 連携 (無料枠)**: 英語論文のタイトルを自然な日本語に自動翻訳し、理学療法士・リハビリ管理職向けの臨床的示唆を含む要約を付与。
- **メール自動配信機能**: 毎朝のダイジェスト（おすすめ5選、AI要約・翻訳、厚労省新着）を指定したメールアドレスへ自動送信。
- **PubMed & OpenAlex 自動取得**: 直近の新着学術論文を自動取得し、DOI・タイトルで重複排除。
- **厚生労働省 制度・診療報酬ニュース**: 公式RSSから診療報酬・医療・介護保険関連の重要通知を自動集約。
- **スマートフォン最適化**: レスポンシブなカード型デザインとリアルタイム用語検索機能。
- **完全自動運用**: GitHub Actions により、毎朝 06:00 (JST) に全自動でビルド＆配信。

---

## ⚙️ GitHub Secrets の設定 (オプション)

リポジトリの **Settings** > **Secrets and variables** > **Actions** に以下を登録することで、AI翻訳・要約およびメール配信が有効になります。

| シークレット名 | 必須 / 任意 | 説明 |
|---|---|---|
| `GEMINI_API_KEY` | 任意 | [Google AI Studio](https://aistudio.google.com/) の無料枠APIキー。英語論文の日本語翻訳＋要約が有効化されます。 |
| `MAIL_TO` | 任意 | 配信先のメールアドレス（カンマ区切りで複数指定可）。設定されている場合のみメール送信が行われます。 |
| `SMTP_USER` | メール送信時必須 | 送信元メールアドレス（例: `your-address@gmail.com`）。 |
| `SMTP_PASSWORD` | メール送信時必須 | 送信元メールのパスワード（Gmailの場合は「アプリパスワード」）。 |
| `SMTP_HOST` | 任意 | SMTPサーバー（デフォルト: `smtp.gmail.com`）。 |
| `SMTP_PORT` | 任意 | SMTPポート番号（デフォルト: `587`）。 |

※未設定の場合でもエラーにならず、安全に該当機能のみをスキップしてWebページ生成が継続します。

---

## 🛠️ ローカルでの実行方法

```powershell
# 文字化け対策
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# データ取得＆HTML生成の実行 (環境変数が設定されていればメール送信も実行)
python main.py
```

`config.yaml` を編集することで、検索キーワードや取得対象期間を簡単にカスタマイズできます。
