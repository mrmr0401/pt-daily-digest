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
        
        all_raw_papers.extend(pubmed_res)
        all_raw_papers.extend(openalex_res)
    
    # 重複除去ロジック
    unique_papers = []
    seen_dois = set()
    seen_titles = set()
    
    for paper in all_raw_papers:
        doi = paper.get("doi")
        title_norm = _normalize_title(paper.get("title", ""))
        
        # 1. DOIによる重複チェック
        if doi and doi in seen_dois:
            continue
            
        # 2. DOIがない場合のタイトル正規化による重複チェック
        if title_norm in seen_titles:
            continue
            
        if doi:
            seen_dois.add(doi)
        if title_norm:
            seen_titles.add(title_norm)
            
        unique_papers.append(paper)
        
    logger.info(f"Total raw papers fetched: {len(all_raw_papers)}, Unique papers: {len(unique_papers)}")
    return unique_papers
