import re
import logging
from typing import List, Dict, Any, Optional
from src.fetcher.pubmed import fetch_pubmed_papers
from src.fetcher.openalex import fetch_openalex_papers
from src.fetcher.jstage import fetch_jstage_papers
from src.utils.translator import is_japanese, get_english_keywords

logger = logging.getLogger(__name__)

def _normalize_title(title: str) -> str:
    """タイトルの比較用正規化 (小文字・アルファベット/数字/ひらがな/カタカナ/漢字のみ)"""
    return re.sub(r'[^a-z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', title.lower())

def fetch_all_papers(keywords: List[str], days_back: int = 7, max_per_keyword: int = 20, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    指定キーワードに基づき、PubMed、OpenAlex、J-STAGE から論文を取得し、DOI・タイトルで名寄せ（重複排除）を行う。
    - 日本語キーワード: J-STAGEで直接検索 + 英語に自動翻訳（手動辞書/キャッシュ/Gemini）してPubMed・OpenAlexでOR検索
    - 英語キーワード: PubMed・OpenAlex・J-STAGEで直接検索
    """
    all_raw_papers = []
    config = config or {}
    manual_translations = config.get("keyword_translations", {})
    
    for kw in keywords:
        clean_kw = kw.strip()
        if not clean_kw:
            continue
            
        logger.info(f"=== Processing keyword: '{clean_kw}' ===")
        
        # 1. 日本語かどうかの判定
        if is_japanese(clean_kw):
            # 日本語キーワードの場合:
            # A. J-STAGE で日本語検索
            logger.info(f"[J-STAGE] Fetching with Japanese keyword: '{clean_kw}'...")
            jstage_res = fetch_jstage_papers(clean_kw, days_back=days_back, max_results=max_per_keyword)
            for p in jstage_res:
                p["matched_keywords"] = [clean_kw]
            all_raw_papers.extend(jstage_res)
            
            # B. 英語への展開 (手動辞書 -> キャッシュ -> Gemini API)
            en_candidates = get_english_keywords(clean_kw, manual_translations=manual_translations)
            logger.info(f"Keyword '{clean_kw}' translated to English candidates: {en_candidates}")
            
            if en_candidates:
                # PubMed: ("candidate1" OR "candidate2")
                if len(en_candidates) > 1:
                    pubmed_query = "(" + " OR ".join([f'"{c}"' for c in en_candidates]) + ")"
                    openalex_query = "|".join(en_candidates)
                else:
                    pubmed_query = f'"{en_candidates[0]}"'
                    openalex_query = en_candidates[0]
                    
                logger.info(f"[PubMed] Fetching with query: {pubmed_query}...")
                pubmed_res = fetch_pubmed_papers(pubmed_query, days_back=days_back, max_results=max_per_keyword)
                for p in pubmed_res:
                    p["matched_keywords"] = [clean_kw]
                all_raw_papers.extend(pubmed_res)
                
                logger.info(f"[OpenAlex] Fetching with query: {openalex_query}...")
                openalex_res = fetch_openalex_papers(openalex_query, days_back=days_back, max_results=max_per_keyword)
                for p in openalex_res:
                    p["matched_keywords"] = [clean_kw]
                all_raw_papers.extend(openalex_res)
            else:
                logger.info(f"No English translation available for '{clean_kw}'. Skipped overseas databases.")
                
        else:
            # 英語キーワードの場合 (最初から英語入力):
            # A. PubMed & OpenAlex で直接検索
            logger.info(f"[PubMed] Fetching with English keyword: '{clean_kw}'...")
            pubmed_res = fetch_pubmed_papers(f'"{clean_kw}"', days_back=days_back, max_results=max_per_keyword)
            for p in pubmed_res:
                p["matched_keywords"] = [clean_kw]
            all_raw_papers.extend(pubmed_res)
            
            logger.info(f"[OpenAlex] Fetching with English keyword: '{clean_kw}'...")
            openalex_res = fetch_openalex_papers(clean_kw, days_back=days_back, max_results=max_per_keyword)
            for p in openalex_res:
                p["matched_keywords"] = [clean_kw]
            all_raw_papers.extend(openalex_res)
            
            # B. J-STAGE でも英語検索
            logger.info(f"[J-STAGE] Fetching with English keyword: '{clean_kw}'...")
            jstage_res = fetch_jstage_papers(clean_kw, days_back=days_back, max_results=max_per_keyword)
            for p in jstage_res:
                p["matched_keywords"] = [clean_kw]
            all_raw_papers.extend(jstage_res)
    
    # 2. 重複除去および情報マージロジック (DOI およびタイトル正規化による名寄せ)
    unique_papers_dict = {} # key -> paper
    
    for paper in all_raw_papers:
        doi = paper.get("doi")
        title_norm = _normalize_title(paper.get("title", ""))
        
        # 名寄せキー (DOI優先、なければ正規化タイトル)
        key = f"doi:{doi.lower()}" if doi else f"title:{title_norm}"
        
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
            # 本文やアブストラクト、オープンアクセス情報の優先採用
            if not existing.get("url") and paper.get("url"):
                existing["url"] = paper.get("url")
            if not existing.get("journal") and paper.get("journal"):
                existing["journal"] = paper.get("journal")
        else:
            unique_papers_dict[key] = paper
            
    unique_papers = list(unique_papers_dict.values())
    logger.info(f"Total raw papers fetched: {len(all_raw_papers)}, Unique papers after deduplication: {len(unique_papers)}")
    return unique_papers
