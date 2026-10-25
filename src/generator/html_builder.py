import os
import json
from datetime import datetime
from typing import List, Dict, Any

def generate_docs(papers: List[Dict[str, Any]], policy_news: List[Dict[str, Any]], recommended: List[Dict[str, Any]] = None, config: Dict[str, Any] = None, docs_dir: str = "docs"):
    """
    docs/data.json と docs/index.html を生成する。
    - 画面最上部: 「今日のおすすめ 5件」 (Gemini AI要約・原文リンク・注記・PDF付き)
    - メインタブ切り替え (制度ニュース / 新着論文)
    - 制度ニュース: 20件ごとのページ分割タブ
    - 新着論文: 日付ごとのグループ分けタブ
    - J-STAGE、PubMed、OpenAlex 対応
    - インクリメンタル用語検索 (フリーワード検索)
    - 検索用語設定モーダル: 日本語・英語対訳キーワード編集 & config.yamlコピー・ダウンロード機能
    """
    os.makedirs(docs_dir, exist_ok=True)
    
    if recommended is None:
        recommended = []
    if config is None:
        config = {}
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.now().strftime("%Y年%m月%d日")
    
    keywords = config.get("keywords", [])
    policy_keywords = config.get("policy_keywords", [])
    keyword_translations = dict(config.get("keyword_translations", {}))
    
    # 翻訳キャッシュ (data/keyword_cache.json) もマージして画面側に渡す
    cache_path = os.path.join("data", "keyword_cache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                for k, v in cached_data.items():
                    if k not in keyword_translations:
                        keyword_translations[k] = v
        except Exception:
            pass
    
    output_data = {
        "generated_at": now_str,
        "keywords": keywords,
        "keyword_translations": keyword_translations,
        "policy_keywords": policy_keywords,
        "recommended_count": len(recommended),
        "policy_news_count": len(policy_news),
        "papers_count": len(papers),
        "combined_pdf_url": config.get("combined_pdf_url", "pdf/pt_digest_top5.pdf"),
        "recommended": recommended,
        "policy_news": policy_news,
        "papers": papers
    }
    
    # 1. docs/data.json 保存
    json_path = os.path.join(docs_dir, "data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    # JSON 埋め込み用文字列
    data_json_str = json.dumps(output_data, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PT情報ダイジェスト | 制度・診療報酬＆新着論文</title>
    <meta name="description" content="理学療法士管理職のための制度・診療報酬ニュースおよび学術論文ダイジェスト">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0b0f19;
            --bg-secondary: #111827;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #38bdf8;
            --accent-policy: #fbbf24;
            --accent-jstage: #f43f5e;
            --accent-openalex: #34d399;
            --accent-pubmed: #38bdf8;
            --font-family: 'Plus Jakarta Sans', 'Noto Sans JP', sans-serif;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: var(--font-family);
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 16px 12px;
            max-width: 800px;
            margin: 0 auto;
        }}

        .app-container {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        /* ヘッダー */
        header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 16px 20px;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
        }}

        .header-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .header-meta {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 4px;
            display: flex;
            gap: 12px;
        }}

        /* 設定ボタン */
        .settings-btn {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.775rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}
        .settings-btn:hover {{
            background: rgba(255, 255, 255, 0.16);
            border-color: var(--accent-primary);
        }}

        /* モーダル */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(6px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            padding: 16px;
        }}
        .modal-content {{
            background: #1e293b;
            border: 1px solid var(--card-border);
            border-radius: 16px;
            max-width: 620px;
            width: 100%;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            animation: modalFadeIn 0.25s ease-out;
        }}
        @keyframes modalFadeIn {{
            from {{ opacity: 0; transform: scale(0.96); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        .modal-header {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .modal-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        .modal-close-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 1.2rem;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 6px;
        }}
        .modal-close-btn:hover {{
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.1);
        }}
        .modal-body {{
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        }}
        .modal-desc {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 16px;
            background: rgba(15, 23, 42, 0.5);
            padding: 10px 14px;
            border-radius: 8px;
            border-left: 3px solid var(--accent-primary);
        }}
        .keyword-section {{
            margin-bottom: 18px;
        }}
        .keyword-section-title {{
            font-size: 0.875rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* キーワードペア表示行 */
        .kw-pair-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 10px;
        }}
        .kw-pair-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 6px 12px;
            gap: 8px;
            font-size: 0.825rem;
        }}
        .kw-pair-main {{
            font-weight: 700;
            color: var(--accent-primary);
            min-width: 90px;
        }}
        .kw-pair-en {{
            flex: 1;
            font-size: 0.775rem;
            color: var(--text-secondary);
            font-style: italic;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .kw-pair-del {{
            cursor: pointer;
            color: #ef4444;
            opacity: 0.7;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .kw-pair-del:hover {{
            opacity: 1;
            background: rgba(239, 68, 68, 0.15);
        }}

        .keyword-input-row {{
            display: flex;
            gap: 6px;
        }}
        .keyword-input {{
            flex: 1;
            padding: 8px 12px;
            background: #0f172a;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 0.85rem;
            outline: none;
        }}
        .keyword-input:focus {{
            border-color: var(--accent-primary);
        }}
        .btn-add {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 0.825rem;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
        }}
        .btn-add:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}

        .keyword-tags-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 8px;
            min-height: 32px;
            padding: 6px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 8px;
            border: 1px dashed var(--card-border);
        }}
        .keyword-tag-badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.35);
            color: #fbbf24;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.775rem;
            font-weight: 600;
        }}
        .tag-remove-btn {{
            cursor: pointer;
            font-size: 0.85rem;
            color: inherit;
            opacity: 0.7;
            padding: 0 2px;
            line-height: 1;
        }}
        .tag-remove-btn:hover {{
            opacity: 1;
            color: #ef4444;
        }}

        /* config.yaml エクスポートセクション */
        .config-export-section {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(251, 191, 36, 0.3);
            border-radius: 10px;
            padding: 14px;
            margin-top: 20px;
        }}
        .config-export-title {{
            font-size: 0.875rem;
            font-weight: 700;
            color: #fbbf24;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .btn-copy-yaml, .btn-download-yaml {{
            background: #1e293b;
            border: 1px solid rgba(251, 191, 36, 0.4);
            color: #f8fafc;
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-copy-yaml:hover, .btn-download-yaml:hover {{
            background: rgba(251, 191, 36, 0.15);
            border-color: #fbbf24;
        }}

        .modal-footer {{
            padding: 14px 20px;
            border-top: 1px solid var(--card-border);
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            background: rgba(15, 23, 42, 0.4);
        }}
        .btn-primary {{
            background: linear-gradient(90deg, #f59e0b, #0284c7);
            color: #ffffff;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: all 0.2s ease;
        }}
        .btn-primary:hover {{
            filter: brightness(1.1);
            transform: translateY(-1px);
        }}
        .btn-secondary {{
            background: transparent;
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
        }}
        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
        }}

        /* 検索ボックス */
        .search-box-container {{
            position: relative;
            margin-bottom: 4px;
        }}
        .search-input {{
            width: 100%;
            padding: 10px 16px 10px 38px;
            background: #1e293b;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 0.875rem;
            outline: none;
            transition: all 0.2s ease;
        }}
        .search-input:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }}
        .search-icon {{
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
        }}

        /* タブ */
        .main-tabs {{
            display: flex;
            gap: 8px;
            background: #0f172a;
            padding: 4px;
            border-radius: 12px;
            border: 1px solid var(--card-border);
        }}
        .tab-btn {{
            flex: 1;
            padding: 10px 14px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 700;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .tab-btn.active-policy {{
            background: var(--accent-policy);
            color: #0f172a;
            box-shadow: 0 2px 8px rgba(251, 191, 36, 0.3);
        }}
        .tab-btn.active-paper {{
            background: var(--accent-primary);
            color: #0f172a;
            box-shadow: 0 2px 8px rgba(56, 189, 248, 0.3);
        }}
        .tab-count {{
            font-size: 0.75rem;
            padding: 2px 6px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.15);
        }}

        /* サブナビ・ピル */
        .sub-nav-container {{
            display: flex;
            align-items: center;
            overflow-x: auto;
            padding-bottom: 4px;
        }}
        .sub-pills {{
            display: flex;
            gap: 6px;
        }}
        .pill-btn {{
            padding: 5px 12px;
            background: #1e293b;
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            border-radius: 20px;
            font-size: 0.775rem;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
        }}
        .pill-btn.active {{
            background: rgba(56, 189, 248, 0.2);
            color: var(--accent-primary);
            border-color: var(--accent-primary);
        }}

        /* カードリスト */
        .card-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        /* 政策ニュースカード */
        .policy-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-left: 4px solid var(--accent-policy);
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        }}
        .news-title {{
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.45;
            margin-bottom: 10px;
        }}
        .news-title a {{
            color: var(--text-primary);
            text-decoration: none;
        }}
        .news-title a:hover {{
            color: var(--accent-policy);
            text-decoration: underline;
        }}

        /* 論文カード */
        .paper-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-left: 4px solid var(--accent-primary);
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        }}
        .paper-card.jstage {{
            border-left-color: var(--accent-jstage);
        }}
        .paper-title {{
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.45;
            margin-bottom: 8px;
        }}
        .paper-title a {{
            color: var(--text-primary);
            text-decoration: none;
        }}
        .paper-title a:hover {{
            color: var(--accent-primary);
            text-decoration: underline;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .source-badge {{
            font-size: 0.675rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 6px;
            color: #ffffff;
            text-transform: uppercase;
        }}

        .badge-mhlw {{ background-color: #d97706; }}
        .badge-pubmed {{ background-color: #0369a1; }}
        .badge-openalex {{ background-color: #047857; }}
        .badge-jstage {{ background-color: #b91c1c; }}

        .pub-date {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .paper-meta {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 10px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        .meta-label {{
            color: #64748b;
            font-weight: 600;
        }}

        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 8px;
            margin-top: 6px;
        }}

        .matched-kw-badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.12);
            color: var(--accent-primary);
            border: 1px solid rgba(56, 189, 248, 0.25);
        }}

        .tag-policy {{
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(245, 158, 11, 0.12);
            color: var(--accent-policy);
            border: 1px solid rgba(245, 158, 11, 0.25);
            margin-right: 4px;
        }}

        .link-btn {{
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--accent-primary);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 8px;
            border-radius: 6px;
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.2);
            transition: all 0.2s ease;
        }}
        .link-btn:hover {{
            background: rgba(56, 189, 248, 0.2);
        }}

        /* ページネーション */
        .pagination-container {{
            display: flex;
            justify-content: center;
            gap: 6px;
            margin-top: 16px;
        }}
        .page-btn {{
            padding: 6px 12px;
            background: #1e293b;
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
        }}
        .page-btn.active {{
            background: var(--accent-policy);
            color: #0f172a;
            border-color: var(--accent-policy);
        }}

        /* おすすめ5選 セクション */
        .recommend-section {{
            margin-bottom: 24px;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
            border: 1px solid rgba(251, 191, 36, 0.35);
            border-radius: 16px;
            padding: 16px 14px;
            box-shadow: 0 10px 25px -5px rgba(245, 158, 11, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        }}
        .recommend-top-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .recommend-heading {{
            font-size: 1.125rem;
            font-weight: 700;
            color: #fbbf24;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .recommend-sub {{
            font-size: 0.725rem;
            color: var(--text-secondary);
            margin-top: 2px;
        }}
        .recommend-toggle-btn {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .recommend-toggle-btn:hover {{
            background: rgba(255, 255, 255, 0.12);
            color: var(--text-primary);
        }}
        .combined-pdf-btn {{
            background: linear-gradient(90deg, #d97706, #b45309);
            color: #ffffff;
            text-decoration: none;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            transition: all 0.2s ease;
        }}
        .combined-pdf-btn:hover {{
            filter: brightness(1.1);
        }}

        .recommend-card {{
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            position: relative;
        }}
        .recommend-card:hover {{
            border-color: rgba(251, 191, 36, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
        }}
        .recommend-rank {{
            font-size: 0.75rem;
            font-weight: 700;
            color: #0f172a;
            background: #fbbf24;
            padding: 2px 8px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-bottom: 6px;
        }}
        .recommend-score {{
            font-size: 0.7rem;
            color: #94a3b8;
            margin-left: 6px;
        }}
        .highlight-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-bottom: 8px;
        }}
        .highlight-tag {{
            font-size: 0.675rem;
            padding: 1px 6px;
            border-radius: 4px;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
        }}
        .highlight-tag.citation {{
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}
        .highlight-tag.new {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .ai-summary-box {{
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.08) 100%);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-left: 3px solid #8b5cf6;
            border-radius: 8px;
            padding: 10px 12px;
            margin: 10px 0;
        }}
        .ai-summary-label {{
            font-size: 0.725rem;
            font-weight: 700;
            color: #c084fc;
            display: flex;
            align-items: center;
            gap: 5px;
            margin-bottom: 5px;
        }}
        .ai-summary-text {{
            font-size: 0.85rem;
            line-height: 1.6;
            color: #f1f5f9;
            margin-bottom: 8px;
        }}
        .ai-disclaimer {{
            font-size: 0.7rem;
            color: #fbbf24;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-weight: 500;
            background: rgba(245, 158, 11, 0.1);
            padding: 2px 7px;
            border-radius: 4px;
            border: 1px solid rgba(245, 158, 11, 0.25);
        }}

        .pdf-download-btn {{
            background-color: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.35);
            text-decoration: none;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s ease;
        }}
        .pdf-download-btn:hover {{
            background-color: rgba(239, 68, 68, 0.25);
        }}

        /* トースト通知 */
        .toast-notification {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: #1e293b;
            color: #f8fafc;
            border: 1px solid var(--accent-primary);
            padding: 12px 20px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            font-size: 0.875rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 10000;
            animation: toastIn 0.3s ease-out;
        }}
        @keyframes toastIn {{
            from {{ transform: translate(-50%, 20px); opacity: 0; }}
            to {{ transform: translate(-50%, 0); opacity: 1; }}
        }}

        footer {{
            text-align: center;
            margin-top: 32px;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <header>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div class="header-title" style="margin-bottom: 0;">📋 PT情報ダイジェスト</div>
                <button id="settingsBtn" class="settings-btn" onclick="openKeywordModal()">⚙️ 検索用語設定</button>
            </div>
            <div class="header-meta">
                <span>更新: {today_date}</span>
                <span>理学療法士管理職向け</span>
            </div>
        </header>

        <!-- 検索用語設定モーダル -->
        <div id="keywordModal" class="modal-overlay" style="display: none;">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title">⚙️ 検索対象用語の設定</div>
                    <button class="modal-close-btn" onclick="closeKeywordModal()">✕</button>
                </div>
                
                <div class="modal-body">
                    <p class="modal-desc">
                        対象とするキーワードを追加・編集できます。<br/>
                        <strong>【学術論文キーワード】</strong>は日本語で登録すると、<strong>J-STAGE（国内学会誌）</strong>で直接検索されるとともに、<strong>英語（PubMed / OpenAlex）</strong>へ自動展開されます（英語候補の編集も可能です）。<br/>
                        設定内容は即座に画面上の絞り込みに反映されるほか、下のボタンから <strong>config.yaml をコピー／ダウンロード</strong> してリポジトリに push することで、毎朝の自動収集にも反映できます。
                    </p>

                    <!-- 学術論文キーワード (日本語 ➔ 英語) -->
                    <div class="keyword-section">
                        <div class="keyword-section-title">📚 学術論文 検索キーワード (J-STAGE / PubMed / OpenAlex)</div>
                        <div id="paperKeywordPairList" class="kw-pair-list"></div>
                        <div class="keyword-input-row">
                            <input type="text" id="newPaperKwInput" class="keyword-input" placeholder="日本語キーワード (例: 呼吸理学療法, 訪問リハビリ...)">
                            <input type="text" id="newPaperEnInput" class="keyword-input" placeholder="英語候補 (任意・カンマ区切り: chest physical therapy)">
                            <button class="btn-add" onclick="addPaperKeyword()">＋ 追加</button>
                        </div>
                    </div>

                    <!-- 制度・診療報酬キーワード -->
                    <div class="keyword-section">
                        <div class="keyword-section-title">🏛️ 制度・診療報酬 検索キーワード (厚労省ニュース)</div>
                        <div id="policyKeywordTags" class="keyword-tags-container"></div>
                        <div class="keyword-input-row">
                            <input type="text" id="newPolicyKwInput" class="keyword-input" placeholder="例: 疾患別リハビリテーション, 疑義解釈..." onkeydown="if(event.key==='Enter') addPolicyKeyword()">
                            <button class="btn-add" onclick="addPolicyKeyword()">＋ 追加</button>
                        </div>
                    </div>

                    <!-- config.yaml 反映・出力セクション -->
                    <div class="config-export-section">
                        <div class="config-export-title">📋 毎朝の自動収集（config.yaml）への反映手順</div>
                        <p style="font-size: 0.775rem; color: var(--text-secondary); margin-bottom: 10px; line-height: 1.5;">
                            画面上で編集した内容はブラウザ内に即時保存されます。毎朝の自動収集（GitHub Actions）にも反映したい場合は、以下のボタンで設定内容を取得し、リポジトリの <code>config.yaml</code> に貼り付けて push してください。
                        </p>
                        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                            <button class="btn-copy-yaml" onclick="copyConfigYaml()">📋 YAMLをコピー</button>
                            <button class="btn-download-yaml" onclick="downloadConfigYaml()">💾 config.yamlをダウンロード</button>
                        </div>
                    </div>
                </div>

                <div class="modal-footer">
                    <button class="btn-secondary" onclick="closeKeywordModal()">閉じる</button>
                    <button class="btn-primary" onclick="saveKeywords()">
                        💾 画面に適用して保存
                    </button>
                </div>
            </div>
        </div>

        <!-- 画面最上部: 今日の注目おすすめ 5選 セクション -->
        <section id="recommendSection" class="recommend-section">
            <div class="recommend-top-bar">
                <div>
                    <div class="recommend-heading">
                        <span>🌟 今日の注目おすすめ 5選</span>
                    </div>
                    <div class="recommend-sub">重要キーワード一致・最新度・被引用数より厳選 / AI日本語要約・翻訳付き</div>
                </div>
                <div style="display:flex; align-items:center; gap:6px;">
                    <a id="combinedPdfBtn" href="{config.get('combined_pdf_url', 'pdf/pt_digest_top5.pdf')}" target="_blank" download class="combined-pdf-btn">
                        📄 5選まとめPDF
                    </a>
                    <button id="toggleRecommendBtn" class="recommend-toggle-btn" onclick="toggleRecommendSection()">折りたたむ ▲</button>
                </div>
            </div>
            <div id="recommendCardList"></div>
        </section>

        <!-- 用語リアルタイム検索窓 -->
        <div class="search-box-container">
            <svg class="search-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input type="text" id="searchInput" class="search-input" placeholder="タイトル・著者・キーワードでリアルタイム検索...">
        </div>

        <!-- メインタブ切り替え -->
        <div class="main-tabs">
            <button id="tabPolicy" class="tab-btn active-policy" onclick="switchMainTab('policy')">
                🏛️ 制度・診療報酬ニュース <span id="countPolicy" class="tab-count">0</span>
            </button>
            <button id="tabPaper" class="tab-btn" onclick="switchMainTab('paper')">
                📚 関連新着論文 <span id="countPaper" class="tab-count">0</span>
            </button>
        </div>

        <!-- サブピル/タブ領域 (制度: 20件ページ別 / 論文: 日付別) -->
        <div id="subNavContainer" class="sub-nav-container">
            <div id="subPills" class="sub-pills"></div>
        </div>

        <!-- コンテンツリスト -->
        <main>
            <div id="contentList" class="card-list"></div>
            <div id="paginationContainer" class="pagination-container"></div>
        </main>

        <footer>
            <p>PT Daily Digest &copy; {datetime.now().year} | 毎朝自動更新</p>
            <p style="margin-top: 6px; font-size: 0.725rem; color: #64748b;">
                学術情報提供元: <a href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank" rel="noopener noreferrer" style="color:var(--accent-pubmed);">PubMed</a> / <a href="https://openalex.org/" target="_blank" rel="noopener noreferrer" style="color:var(--accent-openalex);">OpenAlex</a> / <a href="https://www.jstage.jst.go.jp/" target="_blank" rel="noopener noreferrer" style="color:var(--accent-jstage);">J-STAGE (JST)</a> | 行政情報: <a href="https://www.mhlw.go.jp/" target="_blank" rel="noopener noreferrer" style="color:var(--accent-policy);">厚生労働省</a>
            </p>
        </footer>
    </div>

    <!-- データ埋め込み＆フロントエンドJavaScript -->
    <script>
        const APP_DATA = {data_json_str};

        let currentMainTab = 'policy'; // 'policy' or 'paper'
        let currentPolicyPage = 1;
        const POLICY_PAGE_SIZE = 20;
        let currentPaperDate = 'ALL';
        let searchQuery = '';

        // ユーザー設定キーワード & 対訳辞書 (LocalStorage または APP_DATA から初期化)
        let userPaperKeywords = [];
        let userPolicyKeywords = [];
        let userTranslations = {{}};

        try {{
            const savedPaper = localStorage.getItem('pt_user_keywords_paper');
            const savedPolicy = localStorage.getItem('pt_user_keywords_policy');
            const savedTrans = localStorage.getItem('pt_user_translations');
            
            userPaperKeywords = savedPaper ? JSON.parse(savedPaper) : (APP_DATA.keywords || []);
            userPolicyKeywords = savedPolicy ? JSON.parse(savedPolicy) : (APP_DATA.policy_keywords || []);
            userTranslations = savedTrans ? JSON.parse(savedTrans) : (APP_DATA.keyword_translations || {{}});
        }} catch(e) {{
            userPaperKeywords = APP_DATA.keywords || [];
            userPolicyKeywords = APP_DATA.policy_keywords || [];
            userTranslations = APP_DATA.keyword_translations || {{}};
        }}

        // トースト通知
        function showToast(message) {{
            const existing = document.querySelector('.toast-notification');
            if (existing) existing.remove();
            
            const toast = document.createElement('div');
            toast.className = 'toast-notification';
            toast.innerText = message;
            document.body.appendChild(toast);
            setTimeout(() => {{
                toast.style.transition = 'opacity 0.4s ease';
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 400);
            }}, 3500);
        }}

        // モーダル開閉
        function openKeywordModal() {{
            renderKeywordSettings();
            document.getElementById('keywordModal').style.display = 'flex';
        }}

        function closeKeywordModal() {{
            document.getElementById('keywordModal').style.display = 'none';
        }}

        // 設定の描画
        function renderKeywordSettings() {{
            // 1. 学術論文キーワード一覧 (日本語 ➔ 英語)
            const pairContainer = document.getElementById('paperKeywordPairList');
            if (userPaperKeywords.length === 0) {{
                pairContainer.innerHTML = '<div style="font-size:0.775rem; color:var(--text-secondary); padding:6px;">キーワードがありません</div>';
            }} else {{
                pairContainer.innerHTML = userPaperKeywords.map((kw, idx) => {{
                    const enList = userTranslations[kw] || [];
                    const enText = enList.length > 0 ? enList.join(', ') : '（未変換・AI自動展開）';
                    return `
                    <div class="kw-pair-row">
                        <span class="kw-pair-main" style="cursor:pointer;" onclick="setSearchFilter('${{escapeHtml(kw)}}')">🎯 ${{escapeHtml(kw)}}</span>
                        <span class="kw-pair-en">➔ ${{escapeHtml(enText)}}</span>
                        <span class="kw-pair-del" onclick="removePaperKeyword(${{idx}})" title="削除">✕</span>
                    </div>
                    `;
                }}).join('');
            }}

            // 2. 制度キーワード一覧
            const policyContainer = document.getElementById('policyKeywordTags');
            if (userPolicyKeywords.length === 0) {{
                policyContainer.innerHTML = '<span style="font-size:0.75rem; color:var(--text-secondary);">キーワードがありません</span>';
            }} else {{
                policyContainer.innerHTML = userPolicyKeywords.map((kw, idx) => `
                    <span class="keyword-tag-badge">
                        <span style="cursor:pointer;" onclick="setSearchFilter('${{escapeHtml(kw)}}')">${{escapeHtml(kw)}}</span>
                        <span class="tag-remove-btn" onclick="removePolicyKeyword(${{idx}})">✕</span>
                    </span>
                `).join('');
            }}
        }}

        function addPaperKeyword() {{
            const jaInput = document.getElementById('newPaperKwInput');
            const enInput = document.getElementById('newPaperEnInput');
            const jaVal = jaInput.value.trim();
            const enVal = enInput.value.trim();

            if (!jaVal) return;

            if (!userPaperKeywords.includes(jaVal)) {{
                userPaperKeywords.push(jaVal);
            }}

            if (enVal) {{
                const enList = enVal.split(',').map(s => s.trim()).filter(s => s);
                userTranslations[jaVal] = enList;
            }}

            jaInput.value = '';
            enInput.value = '';
            renderKeywordSettings();
        }}

        function removePaperKeyword(idx) {{
            const kw = userPaperKeywords[idx];
            userPaperKeywords.splice(idx, 1);
            delete userTranslations[kw];
            renderKeywordSettings();
        }}

        function addPolicyKeyword() {{
            const input = document.getElementById('newPolicyKwInput');
            const val = input.value.trim();
            if (!val) return;

            if (!userPolicyKeywords.includes(val)) {{
                userPolicyKeywords.push(val);
                renderKeywordSettings();
            }}
            input.value = '';
        }}

        function removePolicyKeyword(idx) {{
            userPolicyKeywords.splice(idx, 1);
            renderKeywordSettings();
        }}

        function setSearchFilter(keyword) {{
            closeKeywordModal();
            const input = document.getElementById('searchInput');
            input.value = keyword;
            searchQuery = keyword.toLowerCase();
            render();
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        // YAML 内容の生成
        function generateYamlContent() {{
            const kwLines = userPaperKeywords.map(k => `  - "${{k}}"`).join('\\n');
            const transLines = Object.keys(userTranslations).map(k => {{
                const items = userTranslations[k].map(en => `    - "${{en}}"`).join('\\n');
                return `  ${{k}}:\\n${{items}}`;
            }}).join('\\n');
            const policyLines = userPolicyKeywords.map(k => `  - "${{k}}"`).join('\\n');

            return `keywords:\\n${{kwLines}}\\n\\nkeyword_translations:\\n${{transLines}}\\n\\npolicy_keywords:\\n${{policyLines}}\\n\\ndays_back: 14\\nmax_results_per_keyword: 20\\n`;
        }}

        // クリップボードへコピー
        function copyConfigYaml() {{
            const yamlStr = generateYamlContent();
            navigator.clipboard.writeText(yamlStr).then(() => {{
                showToast('📋 config.yaml の設定内容をコピーしました！リポジトリに貼り付けてください。');
            }}).catch(() => {{
                alert(yamlStr);
            }});
        }}

        // config.yaml ダウンロード
        function downloadConfigYaml() {{
            const yamlStr = generateYamlContent();
            const blob = new Blob([yamlStr], {{ type: 'text/yaml;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'config.yaml';
            link.click();
            showToast('💾 config.yaml をダウンロードしました！');
        }}

        // 画面に適用して保存
        function saveKeywords() {{
            localStorage.setItem('pt_user_keywords_paper', JSON.stringify(userPaperKeywords));
            localStorage.setItem('pt_user_keywords_policy', JSON.stringify(userPolicyKeywords));
            localStorage.setItem('pt_user_translations', JSON.stringify(userTranslations));
            
            showToast('💾 設定をブラウザに保存し、画面に反映しました');
            closeKeywordModal();
            render();
        }}

        // 初期化
        document.addEventListener('DOMContentLoaded', () => {{
            const settingsBtn = document.getElementById('settingsBtn');
            if (settingsBtn) {{
                settingsBtn.addEventListener('click', openKeywordModal);
            }}

            document.getElementById('searchInput').addEventListener('input', (e) => {{
                searchQuery = e.target.value.trim().toLowerCase();
                currentPolicyPage = 1;
                render();
            }});

            render();
        }});

        function switchMainTab(tab) {{
            currentMainTab = tab;
            const tabPolicy = document.getElementById('tabPolicy');
            const tabPaper = document.getElementById('tabPaper');

            if (tab === 'policy') {{
                tabPolicy.className = 'tab-btn active-policy';
                tabPaper.className = 'tab-btn';
            }} else {{
                tabPolicy.className = 'tab-btn';
                tabPaper.className = 'tab-btn active-paper';
            }}
            render();
        }}

        // フィルタリング処理
        function getFilteredPolicyNews() {{
            return APP_DATA.policy_news.filter(item => {{
                if (!searchQuery) return true;
                const title = (item.title || '').toLowerCase();
                const kws = (item.matched_keywords || []).join(' ').toLowerCase();
                return title.includes(searchQuery) || kws.includes(searchQuery);
            }});
        }}

        function getFilteredPapers() {{
            return APP_DATA.papers.filter(item => {{
                // 検索クエリフィルタ
                if (searchQuery) {{
                    const title = (item.title || '').toLowerCase();
                    const authors = (item.authors || []).join(' ').toLowerCase();
                    const journal = (item.journal || '').toLowerCase();
                    const kws = (item.matched_keywords || []).join(' ').toLowerCase();
                    const matchSearch = title.includes(searchQuery) || authors.includes(searchQuery) || journal.includes(searchQuery) || kws.includes(searchQuery);
                    if (!matchSearch) return false;
                }}
                // 日付フィルタ
                if (currentPaperDate !== 'ALL') {{
                    const pubdate = item.pubdate || '';
                    if (!pubdate.includes(currentPaperDate)) return false;
                }}
                return true;
            }});
        }}

        let isRecommendCollapsed = false;

        function toggleRecommendSection() {{
            isRecommendCollapsed = !isRecommendCollapsed;
            const cardList = document.getElementById('recommendCardList');
            const btn = document.getElementById('toggleRecommendBtn');
            if (isRecommendCollapsed) {{
                cardList.style.display = 'none';
                btn.innerText = '展開する ▼';
            }} else {{
                cardList.style.display = 'block';
                btn.innerText = '折りたたむ ▲';
            }}
        }}

        function escapeHtml(str) {{
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }}

        // おすすめセクションの描画
        function renderRecommendations() {{
            const recSection = document.getElementById('recommendSection');
            const recContainer = document.getElementById('recommendCardList');
            const items = APP_DATA.recommended || [];

            if (items.length === 0) {{
                recSection.style.display = 'none';
                return;
            }}
            recSection.style.display = 'block';

            // 検索クエリがある場合はおすすめ内も絞り込み
            const filteredItems = items.filter(item => {{
                if (!searchQuery) return true;
                const title = (item.title || '').toLowerCase();
                const transTitle = (item.translated_title || '').toLowerCase();
                const authors = (item.authors || []).join(' ').toLowerCase();
                const kws = (item.matched_keywords || []).join(' ').toLowerCase();
                return title.includes(searchQuery) || transTitle.includes(searchQuery) || authors.includes(searchQuery) || kws.includes(searchQuery);
            }});

            if (filteredItems.length === 0) {{
                recContainer.innerHTML = '<div style="font-size:0.8rem; color:var(--text-secondary); padding:8px;">検索に該当するおすすめはありません</div>';
                return;
            }}

            recContainer.innerHTML = filteredItems.map((item, idx) => {{
                const rank = idx + 1;
                const authorsStr = (item.authors || []).slice(0, 3).join(', ') + ((item.authors || []).length > 3 ? '...' : '');
                
                const highlightsHtml = (item.highlights || []).map(hl => {{
                    let c = '';
                    if (hl.includes('被引用')) c = 'citation';
                    else if (hl.includes('新着')) c = 'new';
                    return `<span class="highlight-tag ${{c}}">${{escapeHtml(hl)}}</span>`;
                }}).join('');

                const displayTitle = item.translated_title ? escapeHtml(item.translated_title) : escapeHtml(item.title);
                const originalTitleHtml = item.translated_title ? `<div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:6px;">原文: ${{escapeHtml(item.title)}}</div>` : '';

                let summaryHtml = '';
                if (item.ai_summary) {{
                    summaryHtml = `
                    <div class="ai-summary-box">
                        <div class="ai-summary-label">
                            <span>✨ AI臨床サマリー (日本語要約)</span>
                        </div>
                        <div class="ai-summary-text">${{escapeHtml(item.ai_summary)}}</div>
                        <div class="ai-disclaimer">⚠️ AI要約のため、重要な臨床判断の際は必ず原文リンクをご確認ください</div>
                    </div>
                    `;
                }}

                let pdfLinkHtml = '';
                if (item.pdf_url) {{
                    pdfLinkHtml = `
                    <a href="${{escapeHtml(item.pdf_url)}}" target="_blank" download class="pdf-download-btn">
                        📥 日本語解説PDF
                    </a>
                    `;
                }}

                const badgeClass = item.source_api === 'PubMed' ? 'badge-pubmed' : (item.source_api === 'J-STAGE' ? 'badge-jstage' : (item.source_api === 'OpenAlex' ? 'badge-openalex' : 'badge-mhlw'));

                return `
                <div class="recommend-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span class="recommend-rank">★ おすすめ ${{rank}}位</span>
                        <div style="display:flex; align-items:center; gap:6px;">
                            <span class="source-badge ${{badgeClass}}">${{escapeHtml(item.source_api || item.source || '注目')}}</span>
                            <span class="recommend-score">スコア: ${{item.total_score || 0}}pt</span>
                        </div>
                    </div>
                    <div class="highlight-tags">${{highlightsHtml}}</div>
                    <h3 style="font-size:0.95rem; font-weight:700; line-height:1.45; margin-bottom:4px;">
                        <a href="${{escapeHtml(item.url)}}" target="_blank" rel="noopener noreferrer" style="color:var(--text-primary); text-decoration:none;">
                            ${{displayTitle}}
                        </a>
                    </h3>
                    ${{originalTitleHtml}}
                    <div style="font-size:0.775rem; color:var(--text-secondary); margin-bottom:6px;">
                        ${{authorsStr ? `<span>${{escapeHtml(authorsStr)}}</span> • ` : ''}}
                        <span>${{escapeHtml(item.journal || '掲載情報なし')}}</span>
                        ${{item.pubdate ? ` • <span>${{escapeHtml(item.pubdate)}}</span>` : ''}}
                    </div>
                    ${{summaryHtml}}
                    <div class="card-footer">
                        <div>
                            ${{pdfLinkHtml}}
                        </div>
                        <a href="${{escapeHtml(item.url)}}" target="_blank" rel="noopener noreferrer" class="link-btn link-btn-recommend">
                            原文を確認 <svg viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zm-9 2h6v2H5v12h12v-6h2v7A1 1 0 0 1 18 21H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/></svg>
                        </a>
                    </div>
                </div>
                `;
            }}).join('');
        }}

        // 全体のメイン描画
        function render() {{
            renderRecommendations();

            const filteredPolicy = getFilteredPolicyNews();
            const filteredPaper = getFilteredPapers();

            document.getElementById('countPolicy').innerText = filteredPolicy.length;
            document.getElementById('countPaper').innerText = filteredPaper.length;

            const subNav = document.getElementById('subNavContainer');
            const subPills = document.getElementById('subPills');
            const paginationContainer = document.getElementById('paginationContainer');
            
            subPills.innerHTML = '';
            paginationContainer.innerHTML = '';

            if (currentMainTab === 'policy') {{
                subNav.style.display = 'none';
                renderPolicy(filteredPolicy);
            }} else {{
                subNav.style.display = 'flex';
                renderPaper(filteredPaper);
            }}
        }}

        // --- 制度ニュース描画 ---
        function renderPolicy(allFilteredNews) {{
            const contentList = document.getElementById('contentList');
            const paginationContainer = document.getElementById('paginationContainer');

            if (allFilteredNews.length === 0) {{
                contentList.innerHTML = '<div class="empty-state">該当する制度ニュースは見つかりませんでした。</div>';
                return;
            }}

            const totalPages = Math.ceil(allFilteredNews.length / POLICY_PAGE_SIZE);
            if (currentPolicyPage > totalPages) currentPolicyPage = 1;

            const startIdx = (currentPolicyPage - 1) * POLICY_PAGE_SIZE;
            const endIdx = startIdx + POLICY_PAGE_SIZE;
            const pageItems = allFilteredNews.slice(startIdx, endIdx);

            let html = '';
            pageItems.forEach(item => {{
                const kwTags = (item.matched_keywords || []).map(kw => `<span class="tag-policy">${{escapeHtml(kw)}}</span>`).join('');
                html += `
                <article class="policy-card">
                    <div class="card-header">
                        <span class="source-badge badge-mhlw">${{escapeHtml(item.source || '厚労省')}}</span>
                        <span class="pub-date">${{escapeHtml(item.pubdate || '')}}</span>
                    </div>
                    <h3 class="news-title">
                        <a href="${{escapeHtml(item.url)}}" target="_blank" rel="noopener noreferrer">${{escapeHtml(item.title)}}</a>
                    </h3>
                    <div class="card-footer">
                        <div>${{kwTags}}</div>
                        <a href="${{escapeHtml(item.url)}}" target="_blank" rel="noopener noreferrer" class="link-btn">
                            公式発表 <svg viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zm-9 2h6v2H5v12h12v-6h2v7A1 1 0 0 1 18 21H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/></svg>
                        </a>
                    </div>
                </article>
                `;
            }});
            contentList.innerHTML = html;

            // ページ送りボタン
            if (totalPages > 1) {{
                let navHtml = '';
                if (currentPolicyPage > 1) {{
                    navHtml += `<button class="page-btn" onclick="currentPolicyPage--; render();">◀ 前の20件</button>`;
                }}
                navHtml += `<span style="font-size:0.8rem; color:var(--text-secondary); align-self:center;">${{currentPolicyPage}} / ${{totalPages}} ページ</span>`;
                if (currentPolicyPage < totalPages) {{
                    navHtml += `<button class="page-btn" onclick="currentPolicyPage++; render();">次の20件 ▶</button>`;
                }}
                paginationContainer.innerHTML = navHtml;
            }}
        }}

        // --- 論文描画 (日付ごとのグループ分けタブ) ---
        function renderPaper(allFilteredPapers) {{
            const subPills = document.getElementById('subPills');
            const contentList = document.getElementById('contentList');

            if (allFilteredPapers.length === 0) {{
                contentList.innerHTML = '<div class="empty-state">該当する論文は見つかりませんでした。</div>';
                return;
            }}

            // 日付グループマップ作成
            const dateMap = {{}};
            allFilteredPapers.forEach(paper => {{
                const d = paper.pubdate || '日付不明';
                if (!dateMap[d]) dateMap[d] = 0;
                dateMap[d]++;
            }});

            const dateList = Object.keys(dateMap).sort().reverse();

            // サブピル (日付タブ)
            const allBtn = document.createElement('button');
            allBtn.className = `pill-btn ${{currentPaperDate === 'ALL' ? 'active' : ''}}`;
            allBtn.innerText = `全件 (${{allFilteredPapers.length}})`;
            allBtn.onclick = () => {{
                currentPaperDate = 'ALL';
                render();
            }};
            subPills.appendChild(allBtn);

            dateList.forEach(d => {{
                const btn = document.createElement('button');
                btn.className = `pill-btn ${{currentPaperDate === d ? 'active' : ''}}`;
                btn.innerText = `${{d}} (${{dateMap[d]}})`;
                btn.onclick = () => {{
                    currentPaperDate = d;
                    render();
                }};
                subPills.appendChild(btn);
            }});

            // 選択日付でのフィルタ
            const displayPapers = getFilteredPapers();

            let html = '';
            displayPapers.forEach(paper => {{
                const authorsStr = (paper.authors || []).slice(0, 3).join(', ') + ((paper.authors || []).length > 3 ? '...' : '');
                
                let badgeClass = 'badge-openalex';
                let linkText = '論文原文';
                if (paper.source_api === 'PubMed') {{
                    badgeClass = 'badge-pubmed';
                    linkText = 'PubMed原文';
                }} else if (paper.source_api === 'J-STAGE') {{
                    badgeClass = 'badge-jstage';
                    linkText = 'J-STAGE論文';
                }}
                
                const matchedHtml = (paper.matched_keywords || []).map(k => `<span class="matched-kw-badge">🎯 ${{escapeHtml(k)}}</span>`).join(' ');
                
                html += `
                <article class="paper-card ${{paper.source_api === 'J-STAGE' ? 'jstage' : ''}}">
                    <div class="card-header">
                        <span class="source-badge ${{badgeClass}}">${{escapeHtml(paper.source_api || 'Paper')}}</span>
                        <span class="pub-date">${{escapeHtml(paper.pubdate || '')}}</span>
                    </div>
                    <h3 class="paper-title">
                        <a href="${{escapeHtml(paper.url)}}" target="_blank" rel="noopener noreferrer">${{escapeHtml(paper.title)}}</a>
                    </h3>
                    <div class="paper-meta">
                        <div><span class="meta-label">著者:</span> ${{escapeHtml(authorsStr) || '情報なし'}}</div>
                        <div><span class="meta-label">雑誌:</span> <em>${{escapeHtml(paper.journal || '掲載誌不明')}}</em></div>
                        ${{paper.doi ? `<div><span class="meta-label">DOI:</span> ${{escapeHtml(paper.doi)}}</div>` : ''}}
                    </div>
                    <div class="card-footer">
                        <div>${{matchedHtml}}</div>
                        <a href="${{escapeHtml(paper.url)}}" target="_blank" rel="noopener noreferrer" class="link-btn">
                            ${{linkText}} <svg viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zm-9 2h6v2H5v12h12v-6h2v7A1 1 0 0 1 18 21H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/></svg>
                        </a>
                    </div>
                </article>
                `;
            }});
            contentList.innerHTML = html;
        }}
    </script>
</body>
</html>
"""

    html_path = os.path.join(docs_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
