import os
import json
from datetime import datetime
from typing import List, Dict, Any

def generate_docs(papers: List[Dict[str, Any]], keywords: List[str], docs_dir: str = "docs"):
    """
    docs/data.json と docs/index.html を生成する
    """
    os.makedirs(docs_dir, exist_ok=True)
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.now().strftime("%Y年%m月%d日")
    
    output_data = {
        "generated_at": now_str,
        "keywords": keywords,
        "count": len(papers),
        "papers": papers
    }
    
    # 1. docs/data.json に保存
    json_path = os.path.join(docs_dir, "data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    # 2. docs/index.html を生成
    html_path = os.path.join(docs_dir, "index.html")
    
    # カードリストの生成
    paper_cards_html = ""
    if not papers:
        paper_cards_html = '<div class="empty-state">直近7日間の新着論文は見つかりませんでした。</div>'
    else:
        for idx, paper in enumerate(papers, 1):
            title = paper.get("title", "No Title")
            authors_list = paper.get("authors", [])
            authors_str = ", ".join(authors_list[:3]) + ("..." if len(authors_list) > 3 else "") if authors_list else "著者情報なし"
            journal = paper.get("journal") or "掲載誌不明"
            pubdate = paper.get("pubdate") or "日付不明"
            url = paper.get("url") or "#"
            source_api = paper.get("source_api", "Paper")
            doi = paper.get("doi") or ""

            badge_class = "badge-pubmed" if source_api == "PubMed" else "badge-openalex"

            paper_cards_html += f"""
            <article class="paper-card">
                <div class="card-header">
                    <span class="source-badge {badge_class}">{source_api}</span>
                    <span class="pub-date"><i class="far fa-calendar-alt"></i> {pubdate}</span>
                </div>
                <h2 class="paper-title">
                    <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
                </h2>
                <div class="paper-meta">
                    <div class="meta-item"><span class="meta-label">著者:</span> {authors_str}</div>
                    <div class="meta-item"><span class="meta-label">雑誌:</span> <em>{journal}</em></div>
                    {f'<div class="meta-item"><span class="meta-label">DOI:</span> {doi}</div>' if doi else ''}
                </div>
                <div class="card-footer">
                    <a href="{url}" target="_blank" rel="noopener noreferrer" class="link-btn">
                        原文を読む <svg class="external-icon" viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zm-9 2h6v2H5v12h12v-6h2v7A1 1 0 0 1 18 21H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/></svg>
                    </a>
                </div>
            </article>
            """

    keywords_badges = "".join([f'<span class="kw-tag">{kw}</span>' for kw in keywords])

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PT情報ダイジェスト | 理学療法新着論文</title>
    <meta name="description" content="理学療法士管理職のための新着論文・制度情報ダイジェスト">
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
            --accent-secondary: #34d399;
            --badge-pubmed-bg: #0369a1;
            --badge-openalex-bg: #047857;
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
            padding: 16px 12px 40px;
            display: flex;
            justify-content: center;
        }}

        .app-container {{
            width: 100%;
            max-width: var(--container-max-width);
        }}

        header {{
            margin-bottom: 24px;
            padding: 20px 16px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }}

        .header-title {{
            font-size: 1.4rem;
            font-weight: 700;
            background: linear-gradient(90deg, #38bdf8, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .header-meta {{
            font-size: 0.825rem;
            color: var(--text-secondary);
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }}

        .keywords-container {{
            margin-top: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .kw-tag {{
            font-size: 0.75rem;
            background-color: rgba(56, 189, 248, 0.1);
            color: var(--accent-primary);
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 500;
        }}

        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            margin: 20px 4px 12px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .count-badge {{
            font-size: 0.8rem;
            background: #334155;
            color: #f1f5f9;
            padding: 2px 10px;
            border-radius: 12px;
        }}

        .paper-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .paper-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 16px;
            transition: transform 0.2s ease, border-color 0.2s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}

        .paper-card:active, .paper-card:hover {{
            border-color: var(--accent-primary);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .source-badge {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-pubmed {{ background-color: var(--badge-pubmed-bg); }}
        .badge-openalex {{ background-color: var(--badge-openalex-bg); }}

        .pub-date {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .paper-title {{
            font-size: 1.05rem;
            font-weight: 700;
            line-height: 1.45;
            margin-bottom: 10px;
        }}

        .paper-title a {{
            color: var(--text-primary);
            text-decoration: none;
        }}

        .paper-title a:hover {{
            color: var(--accent-primary);
            text-decoration: underline;
        }}

        .paper-meta {{
            font-size: 0.825rem;
            color: var(--text-secondary);
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-bottom: 14px;
            background: rgba(15, 23, 42, 0.4);
            padding: 8px 12px;
            border-radius: 8px;
        }}

        .meta-item {{
            word-break: break-word;
        }}

        .meta-label {{
            color: #64748b;
            font-weight: 600;
            margin-right: 4px;
        }}

        .card-footer {{
            display: flex;
            justify-content: flex-end;
        }}

        .link-btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: rgba(56, 189, 248, 0.15);
            color: var(--accent-primary);
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            text-decoration: none;
            transition: background 0.2s ease;
        }}

        .link-btn:hover {{
            background-color: rgba(56, 189, 248, 0.25);
        }}

        .external-icon {{
            display: inline-block;
            vertical-align: middle;
        }}

        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-secondary);
            background: var(--card-bg);
            border-radius: 12px;
            border: 1px dashed var(--card-border);
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
            <div class="header-title">
                📋 PT情報ダイジェスト
            </div>
            <div class="header-meta">
                <span>更新日: {today_date}</span>
                <span>自動更新: 毎朝</span>
            </div>
            <div class="keywords-container">
                {keywords_badges}
            </div>
        </header>

        <main>
            <div class="section-title">
                <span>新着論文 (直近7日間)</span>
                <span class="count-badge">{len(papers)} 件</span>
            </div>

            <section class="paper-list">
                {paper_cards_html}
            </section>
        </main>

        <footer>
            <p>PT Daily Digest &copy; {datetime.now().year} | Free & Open Source</p>
        </footer>
    </div>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
