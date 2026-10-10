# 📋 PT Daily Digest (理学療法士向け情報ダイジェスト)

[![PT Daily Digest Generation](https://github.com/mrmr0401/pt-daily-digest/actions/workflows/daily_digest.yml/badge.svg)](https://github.com/mrmr0401/pt-daily-digest/actions/workflows/daily_digest.yml)

理学療法士（PT）管理職のための、新着論文および医療制度情報を毎朝自動集約しスマートフォン最適化デザインで配信する完全無料のシステムです。

📱 **公開ページ (毎朝自動更新):** [https://mrmr0401.github.io/pt-daily-digest/](https://mrmr0401.github.io/pt-daily-digest/)

---

## 🌟 主な機能

- **PubMed & OpenAlex 自動取得**: 直近7日間の新着論文（ stroke rehabilitation, frailty, physical therapy など）を自動取得。
- **自動重複排除**: DOI およびタイトル正規化により同一論文の重複表示を防止。
- **スマートフォン最適化**: レスポンシブなカード型デザインとダークモード対応 UI。
- **完全自動運用**: GitHub Actions により、毎朝 06:00 (JST) に全自動でビルド＆GitHub Pages に配信。

---

## 🛠️ ローカルでの実行方法

```powershell
# 文字化け対策
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# データ取得＆HTML生成の実行
python main.py
```

`config.yaml` を編集することで、検索キーワードや取得対象期間を簡単にカスタマイズできます。
