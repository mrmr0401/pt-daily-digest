import re
import logging
from datetime import datetime, date
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def _parse_date(date_str: str) -> date:
    """日付文字列（YYYY-MM-DD, YYYY/MM/DD, YYYY Mon DD など）をパースする"""
    if not date_str:
        return date.min
    
    # 1. YYYY-MM-DD または YYYY/MM/DD
    m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
            
    # 2. YYYY Mon DD (例: 2026 Oct 15)
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    m2 = re.search(r'(\d{4})\s+([a-zA-Z]{3})\s+(\d{1,2})', date_str)
    if m2:
        y = int(m2.group(1))
        mon = months.get(m2.group(2).lower(), 1)
        d = int(m2.group(3))
        try:
            return date(y, mon, d)
        except ValueError:
            pass
            
    # 3. YYYY Mon (例: 2026 Oct)
    m3 = re.search(r'(\d{4})\s+([a-zA-Z]{3})', date_str)
    if m3:
        y = int(m3.group(1))
        mon = months.get(m3.group(2).lower(), 1)
        return date(y, mon, 1)

    return date.min

def calculate_item_score(item: Dict[str, Any], item_type: str = "paper") -> Dict[str, Any]:
    """
    1件のアイテム（論文または制度ニュース）に対するおすすめスコアを算出する。
    - キーワード一致数 (matched_keywords)
    - 新しさ (recency)
    - 被引用数 (cited_by_count、取得可能な場合)
    """
    today = date.today()
    pubdate_str = item.get("pubdate", "")
    parsed_date = _parse_date(pubdate_str)
    
    # 1. 新しさスコア (最大20点)
    recency_score = 2
    days_ago = None
    if parsed_date != date.min:
        days_ago = (today - parsed_date).days
        if days_ago <= 0:
            recency_score = 20 # 本日
        elif days_ago == 1:
            recency_score = 17 # 昨日
        elif days_ago == 2:
            recency_score = 14
        elif days_ago == 3:
            recency_score = 11
        elif days_ago <= 7:
            recency_score = max(5, 12 - days_ago)
        elif days_ago <= 14:
            recency_score = max(2, 6 - (days_ago - 7))
        else:
            recency_score = 1
            
    # 2. キーワード一致スコア (1キーワードにつき12点、最大36点)
    matched_kws = item.get("matched_keywords", [])
    kw_count = len(matched_kws)
    kw_score = min(kw_count * 12, 36)
    
    # 3. 被引用数スコア (取得できる場合: 1引用あたり8点、最大32点)
    cited_by_count = int(item.get("cited_by_count", 0) or 0)
    citation_score = min(cited_by_count * 8, 32)
    
    # 厚労省の公式発表・制度通知は重要度ボーナス (政策ニュース: +10点)
    policy_bonus = 10 if item_type == "policy" else 0
    
    # 総合スコア
    total_score = recency_score + kw_score + citation_score + policy_bonus
    
    # スコア理由・ハイライトバッジ
    highlights = []
    if days_ago is not None and days_ago <= 1:
        highlights.append("🆕 新着")
    if kw_count >= 2:
        highlights.append(f"🎯 複数キーワード一致 ({kw_count})")
    elif kw_count == 1:
        highlights.append(f"🎯 {matched_kws[0]}")
    if cited_by_count > 0:
        highlights.append(f"🔥 被引用: {cited_by_count}件")
    if item_type == "policy":
        highlights.append("🏛️ 厚労省公式")
        
    return {
        "total_score": total_score,
        "recency_score": recency_score,
        "kw_score": kw_score,
        "citation_score": citation_score,
        "days_ago": days_ago,
        "highlights": highlights
    }

def select_top_recommendations(
    papers: List[Dict[str, Any]], 
    policy_news: List[Dict[str, Any]], 
    config: Dict[str, Any] = None, 
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    論文および制度ニュースから、スコアリングに基づいて「今日のおすすめN件」を選定する。
    """
    candidates = []
    
    # 論文候補のスコアリング
    for p in papers:
        item_copy = dict(p)
        item_copy["item_type"] = "paper"
        score_info = calculate_item_score(item_copy, item_type="paper")
        item_copy.update(score_info)
        candidates.append(item_copy)
        
    # 制度ニュース候補のスコアリング
    for n in policy_news:
        item_copy = dict(n)
        item_copy["item_type"] = "policy"
        score_info = calculate_item_score(item_copy, item_type="policy")
        item_copy.update(score_info)
        candidates.append(item_copy)
        
    # スコア降順でソート (同点の場合は新しさ、次に被引用数)
    candidates.sort(
        key=lambda x: (
            x.get("total_score", 0),
            -(x.get("days_ago", 999) if x.get("days_ago") is not None else 999),
            x.get("cited_by_count", 0)
        ),
        reverse=True
    )
    
    top_items = candidates[:top_n]
    logger.info(f"Selected {len(top_items)} top recommended items (Top score: {top_items[0]['total_score'] if top_items else 0}).")
    return top_items
