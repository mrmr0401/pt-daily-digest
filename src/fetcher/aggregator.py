import re
import logging
from typing import List, Dict, Any
from src.fetcher.pubmed import fetch_pubmed_papers
from src.fetcher.openalex import fetch_openalex_papers

logger = logging.getLogger(__name__)

def _normalize_title(title: str) -> str:
    """タイトルの比較用正規化 (小文字・アルファベット/数字のみ)"""
    return re.sub(r'[^a-z0-9]', '', title.lower())

def fetch_all_papers(keywords: List[str], days_back: int = 7, max_per_keyword: int = 20) -> List[Dict[str, Any]]:
    """
    指定キーワードに基づき PubMed と OpenAlex から全論文を取得し、DOI・タイトルで重複を除去する
    """
    all_raw_papers = []
    
    for kw in keywords:
        logger.info(f"Fetching papers for keyword: '{kw}'...")
        pubmed_res = fetch_pubmed_papers(kw, days_back=days_back, max_results=max_per_keyword)
        openalex_res = fetch_openalex_papers(kw, days_back=days_back, max_results=max_per_keyword)
        
        for p in pubmed_res:
            p["matched_keywords"] = [kw]
        for p in openalex_res:
            p["matched_keywords"] = [kw]
            
        all_raw_papers.extend(pubmed_res)
        all_raw_papers.extend(openalex_res)
    
    # 重複除去および情報マージロジック
    unique_papers_dict = {} # key -> paper
    
    for paper in all_raw_papers:
        doi = paper.get("doi")
        title_norm = _normalize_title(paper.get("title", ""))
        
        key = f"doi:{doi}" if doi else f"title:{title_norm}"
        
        if key in unique_papers_dict:
            existing = unique_papers_dict[key]
            # matched_keywords の統合
            for kw in paper.get("matched_keywords", []):
                if kw not in existing.get("matched_keywords", []):
                    existing.setdefault("matched_keywords", []).append(kw)
            # cited_by_count の大きい方を採用
            curr_c = paper.get("cited_by_count", 0)
            ex_c = existing.get("cited_by_count", 0)
            if curr_c > ex_c:
                existing["cited_by_count"] = curr_c
        else:
            unique_papers_dict[key] = paper
            
    unique_papers = list(unique_papers_dict.values())
    logger.info(f"Total raw papers fetched: {len(all_raw_papers)}, Unique papers: {len(unique_papers)}")
    return unique_papers
