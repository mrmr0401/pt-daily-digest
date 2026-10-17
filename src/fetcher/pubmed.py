import urllib.request
import urllib.parse
import json
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_pubmed_papers(query: str, days_back: int = 7, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    PubMed (E-utilities) から直近 N 日間の論文を取得する
    """
    papers = []
    
    # 1. esearch で PMID 一覧を取得
    search_term = f'{query} AND ("last {days_back} days"[PDat])'
    params = {
        "db": "pubmed",
        "term": search_term,
        "retmode": "json",
        "retmax": max_results
    }
    
    url_search = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{urllib.parse.urlencode(params)}"
    
    req = urllib.request.Request(
        url_search,
        headers={"User-Agent": "PT-Daily-Digest/1.0 (mailto:admin@example.com)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            id_list = data.get("esearchresult", {}).get("idlist", [])
            
        if not id_list:
            logger.info(f"PubMed: No papers found for query '{query}'")
            return []
            
        # 2. esummary で各論文の詳細情報を取得
        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        url_summary = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{urllib.parse.urlencode(summary_params)}"
        req_summary = urllib.request.Request(
            url_summary,
            headers={"User-Agent": "PT-Daily-Digest/1.0 (mailto:admin@example.com)"}
        )
        
        with urllib.request.urlopen(req_summary, timeout=10) as response:
            sum_data = json.loads(response.read().decode("utf-8"))
            results = sum_data.get("result", {})
            
            for pmid in id_list:
                item = results.get(pmid)
                if not item:
                    continue
                
                title = item.get("title", "").rstrip(".")
                
                # 著者一覧
                authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
                
                # 雑誌名
                journal = item.get("source", "")
                
                # 出版日
                pubdate = item.get("pubdate", "")
                
                # DOI
                doi = None
                article_ids = item.get("articleids", [])
                for aid in article_ids:
                    if aid.get("idtype") == "doi":
                        doi = aid.get("value")
                        break
                
                url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                
                papers.append({
                    "title": title,
                    "authors": authors,
                    "journal": journal,
                    "pubdate": pubdate,
                    "url": url,
                    "doi": doi.lower() if doi else None,
                    "source_api": "PubMed",
                    "pmid": pmid,
                    "cited_by_count": 0
                })
                
    except Exception as e:
        logger.error(f"PubMed API Error ({query}): {e}")
        
    return papers
