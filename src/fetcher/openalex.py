import urllib.request
import urllib.parse
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_openalex_papers(query: str, days_back: int = 7, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    OpenAlex API から直近 N 日間の論文を取得する
    """
    papers = []
    
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    if "|" in query:
        params = {
            "filter": f"default.search:{query},from_publication_date:{start_date}",
            "per_page": max_results,
            "sort": "publication_date:desc"
        }
    else:
        params = {
            "search": query,
            "filter": f"from_publication_date:{start_date}",
            "per_page": max_results,
            "sort": "publication_date:desc"
        }
    
    url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PT-Daily-Digest/1.0 (mailto:admin@example.com)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("results", [])
            
            for item in results:
                title = item.get("title")
                if not title:
                    continue
                
                # DOI
                raw_doi = item.get("doi")
                doi = None
                if raw_doi:
                    doi = raw_doi.replace("https://doi.org/", "").strip()
                
                # 著者一覧
                authorships = item.get("authorships", [])
                authors = [
                    a.get("author", {}).get("display_name", "")
                    for a in authorships
                    if a.get("author", {}).get("display_name")
                ]
                
                # 雑誌名
                primary_loc = item.get("primary_location") or {}
                source = primary_loc.get("source") or {}
                journal = source.get("display_name", "")
                
                # 出版日
                pubdate = item.get("publication_date", "")
                
                # URL
                paper_url = raw_doi if raw_doi else item.get("id", "")
                
                # 被引用数
                cited_by_count = item.get("cited_by_count", 0) or 0

                papers.append({
                    "title": title,
                    "authors": authors,
                    "journal": journal,
                    "pubdate": pubdate,
                    "url": paper_url,
                    "doi": doi.lower() if doi else None,
                    "source_api": "OpenAlex",
                    "openalex_id": item.get("id"),
                    "cited_by_count": cited_by_count
                })
                
    except Exception as e:
        logger.error(f"OpenAlex API Error ({query}): {e}")
        
    return papers
