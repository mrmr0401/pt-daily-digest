import os
import json
from datetime import datetime
from typing import List, Dict, Any

def generate_docs(papers: List[Dict[str, Any]], policy_news: List[Dict[str, Any]], recommended: List[Dict[str, Any]] = None, config: Dict[str, Any] = None, docs_dir: str = "docs"):
    """
    docs/data.json と docs/index.html を生成する。
    - 画面最上部: 「今日のおすすめ 5件」 (Gemini AI要約・原文リンク・注記付き)
    - メインタブ切り替え (制度ニュース / 新着論文)
    - 制度ニュース: 20件ごとのページ分割タブ
    - 新着論文: 日付ごとのグループ分けタブ
    - インクリメンタル用語検索 (フリーワード検索)
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
    
    output_data = {
        "generated_at": now_str,
        "keywords": keywords,
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
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #38bdf8;
            --accent-policy: #f59e0b;
            --accent-recommend: #a855f7;
            --accent-gold: #fbbf24;
            --container-max-width: 680px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 12px 10px 40px;
            display: flex;
            justify-content: center;
        }}

        .app-container {{
            width: 100%;
            max-width: var(--container-max-width);
        }}

        header {{
            margin-bottom: 16px;
            padding: 16px 14px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
        }}

        .header-title {{
            font-size: 1.35rem;
            font-weight: 700;
            background: linear-gradient(90deg, #f59e0b, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
        }}

        .header-meta {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        /* 検索ボックス */
        .search-box-container {{
            margin-bottom: 16px;
            position: relative;
        }}

        .search-input {{
            width: 100%;
            padding: 12px 16px 12px 42px;
            background-color: #1e293b;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            color: var(--text-primary);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }}

        .search-input:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
        }}

        .search-icon {{
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            pointer-events: none;
        }}

        /* メインタブ */
        .main-tabs {{
            display: flex;
            background-color: #1e293b;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 16px;
            gap: 4px;
        }}

        .tab-btn {{
            flex: 1;
            padding: 10px 8px;
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
            gap: 6px;
        }}

        .tab-btn.active-policy {{
            background-color: rgba(245, 158, 11, 0.18);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.4);
        }}

        .tab-btn.active-paper {{
            background-color: rgba(56, 189, 248, 0.18);
            color: var(--accent-primary);
            border: 1px solid rgba(56, 189, 248, 0.4);
        }}

        .tab-count {{
            font-size: 0.75rem;
            padding: 1px 6px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
        }}

        /* サブナビ・フィルター・ページネーション */
        .sub-nav-container {{
            margin-bottom: 16px;
            overflow-x: auto;
            white-space: nowrap;
            padding-bottom: 4px;
            -webkit-overflow-scrolling: touch;
        }}

        .sub-pills {{
            display: inline-flex;
            gap: 6px;
        }}

        .pill-btn {{
            padding: 6px 12px;
            background-color: #1e293b;
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            font-size: 0.8rem;
            font-weight: 600;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .pill-btn.active {{
            background-color: var(--accent-primary);
            color: #0f172a;
            border-color: var(--accent-primary);
        }}

        .pill-btn.active-policy {{
            background-color: var(--accent-policy);
            color: #0f172a;
            border-color: var(--accent-policy);
        }}

        /* コンテンツ領域 */
        .card-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        /* ニュースカード (制度情報) */
        .news-card {{
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

        .pub-date {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .paper-meta {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            display: flex;
            flex-direction: column;
            gap: 2px;
            margin-bottom: 10px;
            background: rgba(15, 23, 42, 0.4);
            padding: 6px 10px;
            border-radius: 6px;
        }}

        .meta-label {{
            color: #64748b;
            font-weight: 600;
            margin-right: 4px;
        }}

        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .tags-group {{
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }}

        .tag-policy {{
            font-size: 0.675rem;
            background: rgba(245, 158, 11, 0.15);
            color: var(--accent-policy);
            border: 1px solid rgba(245, 158, 11, 0.3);
            padding: 1px 5px;
            border-radius: 4px;
        }}

        .link-btn {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background-color: rgba(56, 189, 248, 0.15);
            color: var(--accent-primary);
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 0.775rem;
            font-weight: 600;
            text-decoration: none;
        }}

        .news-card .link-btn {{
            background-color: rgba(245, 158, 11, 0.15);
            color: var(--accent-policy);
            border-color: rgba(245, 158, 11, 0.3);
        }}

        .empty-state {{
            text-align: center;
            padding: 30px 16px;
            color: var(--text-secondary);
            background: var(--card-bg);
            border-radius: 12px;
            border: 1px dashed var(--card-border);
            font-size: 0.875rem;
        }}

        /* ページネーションコントロール */
        .pagination-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 6px;
            margin-top: 16px;
            flex-wrap: wrap;
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

        /* 今日の注目おすすめ 5選 セクション */
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
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.25);
        }}

        .recommend-card:last-child {{
            margin-bottom: 0;
        }}

        .recommend-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .recommend-badges {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}

        .rank-badge {{
            font-size: 0.725rem;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 3px;
        }}

        .rank-1 {{ background: linear-gradient(135deg, #f59e0b, #d97706); color: #ffffff; }}
        .rank-2 {{ background: linear-gradient(135deg, #94a3b8, #64748b); color: #ffffff; }}
        .rank-3 {{ background: linear-gradient(135deg, #b45309, #78350f); color: #ffffff; }}
        .rank-other {{ background: rgba(56, 189, 248, 0.15); color: var(--accent-primary); border: 1px solid rgba(56, 189, 248, 0.3); }}

        .score-pill {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 1px 7px;
            border-radius: 12px;
            background: rgba(251, 191, 36, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.3);
        }}

        .highlight-tag {{
            font-size: 0.675rem;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
        }}

        .highlight-tag.hot {{
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .highlight-tag.new {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        /* AI要約ボックス */
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
            letter-spacing: 0.02em;
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

        .link-btn-recommend {{
            background-color: rgba(251, 191, 36, 0.15) !important;
            color: #fbbf24 !important;
            border-color: rgba(251, 191, 36, 0.35) !important;
        }}

        .link-btn-recommend:hover {{
            background-color: rgba(251, 191, 36, 0.25) !important;
        }}

        .link-btn-pdf {{
            background-color: rgba(139, 92, 246, 0.15) !important;
            color: #c084fc !important;
            border-color: rgba(139, 92, 246, 0.35) !important;
        }}

        .link-btn-pdf:hover {{
            background-color: rgba(139, 92, 246, 0.25) !important;
        }}

        .combined-pdf-btn {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.22) 0%, rgba(217, 119, 6, 0.18) 100%);
            border: 1px solid rgba(251, 191, 36, 0.5);
            color: #fbbf24;
            padding: 5px 11px;
            border-radius: 8px;
            font-size: 0.775rem;
            font-weight: 700;
            text-decoration: none;
            transition: all 0.2s ease;
        }}

        .combined-pdf-btn:hover {{
            background: rgba(245, 158, 11, 0.35);
            box-shadow: 0 0 10px rgba(251, 191, 36, 0.25);
            color: #ffffff;
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
            max-width: 580px;
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
            font-size: 0.825rem;
            color: var(--text-secondary);
            line-height: 1.5;
            margin-bottom: 16px;
            background: rgba(15, 23, 42, 0.4);
            padding: 10px 12px;
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
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: var(--accent-primary);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.775rem;
            font-weight: 600;
        }}
        .keyword-tag-badge.policy {{
            background: rgba(245, 158, 11, 0.15);
            border-color: rgba(245, 158, 11, 0.35);
            color: #fbbf24;
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
        .github-sync-section {{
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(251, 191, 36, 0.3);
            border-radius: 10px;
            padding: 12px;
            margin-top: 20px;
        }}
        .github-sync-title {{
            font-size: 0.85rem;
            font-weight: 700;
            color: #fbbf24;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .btn-save-token {{
            background: #334155;
            border: 1px solid var(--card-border);
            color: #fff;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            cursor: pointer;
        }}
        .btn-save-token:hover {{
            background: #475569;
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
                <button class="settings-btn" onclick="openKeywordModal()">⚙️ 検索用語設定</button>
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
                        対象とするキーワードを自由に追加・削除できます。<br/>
                        設定したキーワードは即座に画面上で絞り込みに使えるほか、GitHubと自動同期して毎朝の自動収集対象（config.yaml）を更新できます。
                    </p>

                    <!-- 英語論文キーワード -->
                    <div class="keyword-section">
                        <div class="keyword-section-title">📚 学術論文 検索キーワード (英語)</div>
                        <div id="paperKeywordTags" class="keyword-tags-container"></div>
                        <div class="keyword-input-row">
                            <input type="text" id="newPaperKwInput" class="keyword-input" placeholder="例: cardiac rehabilitation, dysphagia..." onkeydown="if(event.key==='Enter') addKeyword('paper')">
                            <button class="btn-add" onclick="addKeyword('paper')">＋ 追加</button>
                        </div>
                    </div>

                    <!-- 制度・診療報酬キーワード -->
                    <div class="keyword-section">
                        <div class="keyword-section-title">🏛️ 制度・診療報酬 検索キーワード (日本語)</div>
                        <div id="policyKeywordTags" class="keyword-tags-container"></div>
                        <div class="keyword-input-row">
                            <input type="text" id="newPolicyKwInput" class="keyword-input" placeholder="例: 訪問リハビリ, 摂食嚥下, 回復期..." onkeydown="if(event.key==='Enter') addKeyword('policy')">
                            <button class="btn-add" onclick="addKeyword('policy')">＋ 追加</button>
                        </div>
                    </div>

                    <!-- GitHub自動同期設定 -->
                    <div class="github-sync-section">
                        <div class="github-sync-title">🔄 GitHub 自動同期 (config.yaml 更新＆即時再ビルド)</div>
                        <p style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 8px;">
                            変更を毎朝の自動収集（config.yaml）に反映するには、初回のみ GitHub Personal Access Token を設定してください（ブラウザ内に安全に保存されます）。
                        </p>
                        <div style="display: flex; gap: 6px; margin-bottom: 6px;">
                            <input type="password" id="githubTokenInput" class="keyword-input" placeholder="ghp_xxxxxxxxxxxx (GitHub PAT)" style="font-family: monospace;">
                            <button class="btn-save-token" onclick="saveGithubToken()">保存</button>
                        </div>
                        <div id="tokenStatus" style="font-size: 0.725rem; color: #10b981; margin-bottom: 8px;"></div>
                        <div style="font-size: 0.7rem; color: #94a3b8;">
                            👉 <a href="https://github.com/settings/tokens/new?scopes=repo,workflow&description=PT-Daily-Digest" target="_blank" style="color: var(--accent-primary);">ここからトークンを作成 (repo, workflow 権限)</a>
                        </div>
                    </div>
                </div>

                <div class="modal-footer">
                    <button class="btn-secondary" onclick="closeKeywordModal()">キャンセル</button>
                    <button class="btn-primary" onclick="applyAndSyncKeywords()">
                        🚀 設定を保存してGitHubと自動同期
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

        // ユーザー設定キーワード (LocalStorage または APP_DATA から初期化)
        let userPaperKeywords = [];
        let userPolicyKeywords = [];
        try {{
            const savedPaper = localStorage.getItem('pt_user_keywords_paper');
            const savedPolicy = localStorage.getItem('pt_user_keywords_policy');
            userPaperKeywords = savedPaper ? JSON.parse(savedPaper) : (APP_DATA.keywords || []);
            userPolicyKeywords = savedPolicy ? JSON.parse(savedPolicy) : (APP_DATA.policy_keywords || []);
        }} catch(e) {{
            userPaperKeywords = APP_DATA.keywords || [];
            userPolicyKeywords = APP_DATA.policy_keywords || [];
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
            renderKeywordTags();
            updateTokenStatus();
            document.getElementById('keywordModal').style.display = 'flex';
        }}

        function closeKeywordModal() {{
            document.getElementById('keywordModal').style.display = 'none';
        }}

        function updateTokenStatus() {{
            const token = localStorage.getItem('pt_github_token');
            const statusEl = document.getElementById('tokenStatus');
            const inputEl = document.getElementById('githubTokenInput');
            if (token) {{
                statusEl.innerText = '✅ GitHub Tokenが保存されています（自動同期が有効です）';
                inputEl.value = token;
            }} else {{
                statusEl.innerText = '※ Token未設定: ブラウザ内保存のみ動作します';
            }}
        }}

        function saveGithubToken() {{
            const input = document.getElementById('githubTokenInput');
            const token = input.value.trim();
            if (token) {{
                localStorage.setItem('pt_github_token', token);
                updateTokenStatus();
                showToast('GitHub Tokenをブラウザに保存しました');
            }} else {{
                localStorage.removeItem('pt_github_token');
                updateTokenStatus();
                showToast('GitHub Tokenを解除しました');
            }}
        }}

        // タグのレンダリング
        function renderKeywordTags() {{
            const paperContainer = document.getElementById('paperKeywordTags');
            const policyContainer = document.getElementById('policyKeywordTags');

            paperContainer.innerHTML = userPaperKeywords.map((kw, idx) => `
                <span class="keyword-tag-badge">
                    <span style="cursor:pointer;" onclick="setSearchFilter('${{escapeHtml(kw)}}')">${{escapeHtml(kw)}}</span>
                    <span class="tag-remove-btn" onclick="removeKeyword('paper', ${{idx}})">✕</span>
                </span>
            `).join('') || '<span style="font-size:0.75rem; color:var(--text-secondary);">キーワードがありません</span>';

            policyContainer.innerHTML = userPolicyKeywords.map((kw, idx) => `
                <span class="keyword-tag-badge policy">
                    <span style="cursor:pointer;" onclick="setSearchFilter('${{escapeHtml(kw)}}')">${{escapeHtml(kw)}}</span>
                    <span class="tag-remove-btn" onclick="removeKeyword('policy', ${{idx}})">✕</span>
                </span>
            `).join('') || '<span style="font-size:0.75rem; color:var(--text-secondary);">キーワードがありません</span>';
        }}

        function addKeyword(type) {{
            const inputId = type === 'paper' ? 'newPaperKwInput' : 'newPolicyKwInput';
            const input = document.getElementById(inputId);
            const val = input.value.trim();
            if (!val) return;

            const targetList = type === 'paper' ? userPaperKeywords : userPolicyKeywords;
            if (!targetList.includes(val)) {{
                targetList.push(val);
                renderKeywordTags();
            }}
            input.value = '';
        }}

        function removeKeyword(type, index) {{
            const targetList = type === 'paper' ? userPaperKeywords : userPolicyKeywords;
            targetList.splice(index, 1);
            renderKeywordTags();
        }}

        function setSearchFilter(keyword) {{
            closeKeywordModal();
            const input = document.getElementById('searchInput');
            input.value = keyword;
            searchQuery = keyword.toLowerCase();
            render();
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        // 設定の保存 & GitHub自動同期
        async function applyAndSyncKeywords() {{
            // 1. LocalStorageへ保存
            localStorage.setItem('pt_user_keywords_paper', JSON.stringify(userPaperKeywords));
            localStorage.setItem('pt_user_keywords_policy', JSON.stringify(userPolicyKeywords));

            const token = localStorage.getItem('pt_github_token');
            const saveBtn = document.querySelector('.modal-footer .btn-primary');

            if (!token) {{
                showToast('💾 キーワードを保存しました (GitHub同期用Tokenは未設定です)');
                closeKeywordModal();
                render();
                return;
            }}

            // 2. GitHub REST API で config.yaml を自動コミット
            saveBtn.disabled = true;
            saveBtn.innerText = '⏳ GitHub同期中...';

            const owner = 'mrmr0401';
            const repo = 'pt-daily-digest';
            const filePath = 'config.yaml';
            const apiUrl = `https://api.github.com/repos/${{owner}}/${{repo}}/contents/${{filePath}}`;

            try {{
                // 現在のファイルのSHAを取得
                const getRes = await fetch(apiUrl, {{
                    headers: {{
                        'Authorization': `token ${{token}}`,
                        'Accept': 'application/vnd.github.v3+json'
                    }}
                }});

                if (!getRes.ok) {{
                    throw new Error(`config.yamlの取得に失敗しました (${{getRes.status}}) - Tokenの権限をご確認ください`);
                }}

                const fileData = await getRes.json();
                const currentSha = fileData.sha;

                // 新しい YAML 内容の生成
                const yamlContent = `keywords:\n${{userPaperKeywords.map(k => `  - "${{k}}"`).join('\n')}}\n\npolicy_keywords:\n${{userPolicyKeywords.map(k => `  - "${{k}}"`).join('\n')}}\n\ndays_back: 14\nmax_results_per_keyword: 20\n`;
                
                // Base64エンコード (UTF-8安全)
                const utf8Bytes = new TextEncoder().encode(yamlContent);
                let binaryStr = '';
                utf8Bytes.forEach(b => binaryStr += String.fromCharCode(b));
                const base64Content = btoa(binaryStr);

                // PUT リクエストでコミット
                const putRes = await fetch(apiUrl, {{
                    method: 'PUT',
                    headers: {{
                        'Authorization': `token ${{token}}`,
                        'Accept': 'application/vnd.github.v3+json',
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        message: 'chore: update search keywords from website',
                        content: base64Content,
                        sha: currentSha
                    }})
                }});

                if (!putRes.ok) {{
                    throw new Error(`config.yamlの更新に失敗しました (${{putRes.status}})`);
                }}

                showToast('🚀 config.yamlを更新しました！GitHub Actionsの自動再取得が開始されます。');
                closeKeywordModal();
                render();
            }} catch (err) {{
                console.error(err);
                alert(`GitHub自動同期エラー: ${{err.message}}`);
            }} finally {{
                saveBtn.disabled = false;
                saveBtn.innerText = '🚀 設定を保存してGitHubと自動同期';
            }}
        }}

        // 初期化
        document.addEventListener('DOMContentLoaded', () => {{
            document.getElementById('searchInput').addEventListener('input', (e) => {{
                searchQuery = e.target.value.trim().toLowerCase();
                currentPolicyPage = 1; // 検索時は先頭ページに戻す
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
                    const matchSearch = title.includes(searchQuery) || authors.includes(searchQuery) || journal.includes(searchQuery);
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
                const authors = (item.authors || []).join(' ').toLowerCase();
                const kws = (item.matched_keywords || []).join(' ').toLowerCase();
                const summary = (item.ai_summary || '').toLowerCase();
                return title.includes(searchQuery) || authors.includes(searchQuery) || kws.includes(searchQuery) || summary.includes(searchQuery);
            }});

            if (filteredItems.length === 0) {{
                recContainer.innerHTML = '<div class="empty-state" style="padding: 16px; margin-top: 8px;">検索条件に一致するおすすめはありません。</div>';
                return;
            }}

            let html = '';
            filteredItems.forEach((item, index) => {{
                const rankNum = index + 1;
                let rankClass = 'rank-other';
                let rankText = `#${{rankNum}}`;
                if (rankNum === 1) {{ rankClass = 'rank-1'; rankText = '🥇 #1'; }}
                else if (rankNum === 2) {{ rankClass = 'rank-2'; rankText = '🥈 #2'; }}
                else if (rankNum === 3) {{ rankClass = 'rank-3'; rankText = '🥉 #3'; }}

                const isPolicy = item.item_type === 'policy';
                const sourceBadge = isPolicy
                    ? '<span class="source-badge badge-mhlw">厚生労働省</span>'
                    : `<span class="source-badge ${{item.source_api === 'PubMed' ? 'badge-pubmed' : 'badge-openalex'}}">${{item.source_api || 'Paper'}}</span>`;

                const highlightTags = (item.highlights || []).map(h => {{
                    let tagClass = 'highlight-tag';
                    if (h.includes('新着')) tagClass += ' new';
                    if (h.includes('被引用')) tagClass += ' hot';
                    return `<span class="${{tagClass}}">${{escapeHtml(h)}}</span>`;
                }}).join('');

                const authorsStr = (item.authors || []).slice(0, 3).join(', ') + ((item.authors || []).length > 3 ? '...' : '');

                // タイトル表示（翻訳タイトルがある場合は日本語をメイン、原題をサブに）
                let titleHtml = '';
                if (item.translated_title) {{
                    titleHtml = `
                    <div style="margin-bottom: 8px;">
                        <h3 class="news-title" style="margin-bottom: 4px;">
                            <a href="${{item.url}}" target="_blank" rel="noopener noreferrer">${{escapeHtml(item.translated_title)}}</a>
                        </h3>
                        <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.4;">
                            <span class="meta-label">原題:</span> <em>${{escapeHtml(item.title)}}</em>
                        </div>
                    </div>
                    `;
                }} else {{
                    titleHtml = `
                    <h3 class="news-title" style="margin-bottom: 6px;">
                        <a href="${{item.url}}" target="_blank" rel="noopener noreferrer">${{escapeHtml(item.title)}}</a>
                    </h3>
                    `;
                }}

                // AI要約ブロックの有無判定
                let aiSummaryHtml = '';
                if (item.ai_summary) {{
                    const disclaimerText = item.translated_title 
                        ? '⚠️ AI要約・翻訳のため原文で確認してください'
                        : '⚠️ AI要約のため原文で確認してください';
                    aiSummaryHtml = `
                    <div class="ai-summary-box">
                        <div class="ai-summary-label">
                            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2M7.5 13A2.5 2.5 0 0 0 5 15.5 2.5 2.5 0 0 0 7.5 18a2.5 2.5 0 0 0 2.5-2.5A2.5 2.5 0 0 0 7.5 13m9 0a2.5 2.5 0 0 0-2.5 2.5 2.5 2.5 0 0 0 2.5 2.5 2.5 2.5 0 0 0 2.5-2.5 2.5 2.5 0 0 0-2.5-2.5"/></svg>
                            AIによる要約 (Gemini)
                        </div>
                        <p class="ai-summary-text">${{escapeHtml(item.ai_summary)}}</p>
                        <div class="ai-disclaimer">
                            ${{disclaimerText}}
                        </div>
                    </div>
                    `;
                }}

                html += `
                <article class="recommend-card">
                    <div class="recommend-card-header">
                        <div class="recommend-badges">
                            <span class="rank-badge ${{rankClass}}">${{rankText}}</span>
                            ${{sourceBadge}}
                            <span class="score-pill">⭐ ${{item.total_score || 0}}pt</span>
                        </div>
                        <div style="display:flex; gap:4px; flex-wrap:wrap;">
                            ${{highlightTags}}
                        </div>
                    </div>
                    ${{titleHtml}}
                    ${{!isPolicy ? `
                    <div class="paper-meta" style="margin-bottom: 6px;">
                        <div><span class="meta-label">著者:</span> ${{escapeHtml(authorsStr || '情報なし')}}</div>
                        <div><span class="meta-label">雑誌:</span> <em>${{escapeHtml(item.journal || '掲載誌不明')}}</em></div>
                    </div>
                    ` : ''}}
                    ${{aiSummaryHtml}}
                    <div class="card-footer" style="margin-top: 8px;">
                        <span class="pub-date">${{item.pubdate || ''}}</span>
                        <div style="display:flex; gap:6px; align-items:center;">
                            ${{item.pdf_url ? `
                            <a href="${{item.pdf_url}}" target="_blank" download class="link-btn link-btn-pdf">
                                📄 日本語PDF <svg viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
                            </a>
                            ` : ''}}
                            <a href="${{item.url}}" target="_blank" rel="noopener noreferrer" class="link-btn link-btn-recommend">
                                原文を見る <svg viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zm-9 2h6v2H5v12h12v-6h2v7A1 1 0 0 1 18 21H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/></svg>
                            </a>
                        </div>
                    </div>
                </article>
                `;
            }});
            recContainer.innerHTML = html;
        }}

        function render() {{
            renderRecommendations();

            const filteredPolicy = getFilteredPolicyNews();
            const filteredPaperAll = APP_DATA.papers.filter(item => {{
                if (!searchQuery) return true;
                const title = (item.title || '').toLowerCase();
                const authors = (item.authors || []).join(' ').toLowerCase();
                const journal = (item.journal || '').toLowerCase();
                return title.includes(searchQuery) || authors.includes(searchQuery) || journal.includes(searchQuery);
            }});

            // カウント更新
            document.getElementById('countPolicy').innerText = filteredPolicy.length;
            document.getElementById('countPaper').innerText = filteredPaperAll.length;

            const subPills = document.getElementById('subPills');
            const contentList = document.getElementById('contentList');
            const paginationContainer = document.getElementById('paginationContainer');

            subPills.innerHTML = '';
            contentList.innerHTML = '';
            paginationContainer.innerHTML = '';

            if (currentMainTab === 'policy') {{
                // 制度ニュース render
                renderPolicy(filteredPolicy);
            }} else {{
                // 論文 render
                renderPaper(filteredPaperAll);
            }}
        }}

        // --- 制度ニュース描画 (20件ごとのページ分け) ---
        function renderPolicy(newsList) {{
            const subPills = document.getElementById('subPills');
            const contentList = document.getElementById('contentList');
            const paginationContainer = document.getElementById('paginationContainer');

            if (newsList.length === 0) {{
                contentList.innerHTML = '<div class="empty-state">該当する制度・診療報酬ニュースは見つかりませんでした。</div>';
                return;
            }}

            const totalPages = Math.ceil(newsList.length / POLICY_PAGE_SIZE);
            if (currentPolicyPage > totalPages) currentPolicyPage = 1;

            // サブピル (ページ選択)
            for (let p = 1; p <= totalPages; p++) {{
                const btn = document.createElement('button');
                btn.className = `pill-btn ${{p === currentPolicyPage ? 'active-policy' : ''}}`;
                btn.innerText = `ページ ${{p}} (${{(p-1)*POLICY_PAGE_SIZE + 1}}〜${{Math.min(p*POLICY_PAGE_SIZE, newsList.length)}}件)`;
                btn.onclick = () => {{
                    currentPolicyPage = p;
                    render();
                }};
                subPills.appendChild(btn);
            }}

            // スライス表示
            const startIndex = (currentPolicyPage - 1) * POLICY_PAGE_SIZE;
            const pageItems = newsList.slice(startIndex, startIndex + POLICY_PAGE_SIZE);

            let html = '';
            pageItems.forEach(item => {{
                const kwTags = (item.matched_keywords || []).map(kw => `<span class="tag-policy">${{kw}}</span>`).join('');
                html += `
                <article class="news-card">
                    <div class="card-header">
                        <span class="source-badge badge-mhlw">${{item.source || '厚生労働省'}}</span>
                        <span class="pub-date">${{item.pubdate || ''}}</span>
                    </div>
                    <h3 class="news-title">
                        <a href="${{item.url}}" target="_blank" rel="noopener noreferrer">${{item.title}}</a>
                    </h3>
                    <div class="card-footer">
                        <div class="tags-group">${{kwTags}}</div>
                        <a href="${{item.url}}" target="_blank" rel="noopener noreferrer" class="link-btn">
                            原文を見る <svg viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zm-9 2h6v2H5v12h12v-6h2v7A1 1 0 0 1 18 21H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/></svg>
                        </a>
                    </div>
                </article>
                `;
            }});
            contentList.innerHTML = html;

            // ページネーションボタン (前へ / 次へ)
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
                const badgeClass = paper.source_api === 'PubMed' ? 'badge-pubmed' : 'badge-openalex';
                
                html += `
                <article class="paper-card">
                    <div class="card-header">
                        <span class="source-badge ${{badgeClass}}">${{paper.source_api || 'Paper'}}</span>
                        <span class="pub-date">${{paper.pubdate || ''}}</span>
                    </div>
                    <h3 class="paper-title">
                        <a href="${{paper.url}}" target="_blank" rel="noopener noreferrer">${{paper.title}}</a>
                    </h3>
                    <div class="paper-meta">
                        <div><span class="meta-label">著者:</span> ${{authorsStr || '情報なし'}}</div>
                        <div><span class="meta-label">雑誌:</span> <em>${{paper.journal || '掲載誌不明'}}</em></div>
                        ${{paper.doi ? `<div><span class="meta-label">DOI:</span> ${{paper.doi}}</div>` : ''}}
                    </div>
                    <div class="card-footer">
                        <div></div>
                        <a href="${{paper.url}}" target="_blank" rel="noopener noreferrer" class="link-btn">
                            論文原文 <svg viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zm-9 2h6v2H5v12h12v-6h2v7A1 1 0 0 1 18 21H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/></svg>
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
