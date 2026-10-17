import os
import json
from datetime import datetime
from typing import List, Dict, Any

def generate_docs(papers: List[Dict[str, Any]], policy_news: List[Dict[str, Any]], config: Dict[str, Any], docs_dir: str = "docs"):
    """
    docs/data.json と docs/index.html を生成する。
    - メインタブ切り替え (制度ニュース / 新着論文)
    - 制度ニュース: 20件ごとのページ分割タブ
    - 新着論文: 日付ごとのグループ分けタブ
    - インクリメンタル用語検索 (フリーワード検索)
    """
    os.makedirs(docs_dir, exist_ok=True)
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.now().strftime("%Y年%m月%d日")
    
    keywords = config.get("keywords", [])
    policy_keywords = config.get("policy_keywords", [])
    
    output_data = {
        "generated_at": now_str,
        "keywords": keywords,
        "policy_keywords": policy_keywords,
        "policy_news_count": len(policy_news),
        "papers_count": len(papers),
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
            <div class="header-title">📋 PT情報ダイジェスト</div>
            <div class="header-meta">
                <span>更新: {today_date}</span>
                <span>理学療法士管理職向け</span>
            </div>
        </header>

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

        function render() {{
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
