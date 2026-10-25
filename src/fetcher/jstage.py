import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

USER_AGENT = "PT-Daily-Digest/1.0 (mailto:admin@example.com)"
BASE_URL = "https://api.jstage.jst.go.jp/searchapi/do"

def fetch_jstage_papers(keyword: str, days_back: int = 14, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    J-STAGE Web API から指定キーワードの最新論文を取得する。
    利用規約に基づき、取得項目はタイトル・著者・雑誌名・発行日・DOI・URLに限定し、抄録の全文転載は行わない。
    """
    papers = []
    current_year = datetime.now().year
    
    # 検索パラメータの構築 (service=3: 論文検索)
    # 直近の発行年 (今年および前年)
    params = {
        "service": "3",
        "keyword": keyword,
        "pubyearfrom": str(current_year - 1),
        "pubyearto": str(current_year),
        "count": str(max_results)
    }
    
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    
    try:
        # サーバー負荷への配慮 (アクセス間隔の確保)
        time.sleep(1.0)
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
            
        root = ET.fromstring(xml_data)
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        
        for entry in entries:
            # タイトル (日本語優先、なければ英語または通常タイトル)
            title = ""
            ja_title_el = entry.find('{http://www.w3.org/2005/Atom}article_title/{http://www.w3.org/2005/Atom}ja')
            if ja_title_el is not None and ja_title_el.text:
                title = ja_title_el.text.strip()
            if not title:
                title_el = entry.find('{http://www.w3.org/2005/Atom}title')
                if title_el is not None and title_el.text:
                    title = title_el.text.strip()
            if not title:
                en_title_el = entry.find('{http://www.w3.org/2005/Atom}article_title/{http://www.w3.org/2005/Atom}en')
                if en_title_el is not None and en_title_el.text:
                    title = en_title_el.text.strip()
            if not title:
                continue
                
            # URL (公式記事リンク)
            link = ""
            ja_link_el = entry.find('{http://www.w3.org/2005/Atom}article_link/{http://www.w3.org/2005/Atom}ja')
            if ja_link_el is not None and ja_link_el.text:
                link = ja_link_el.text.strip()
            if not link:
                link_el = entry.find('{http://www.w3.org/2005/Atom}link')
                if link_el is not None:
                    link = link_el.attrib.get('href', '').strip()
            if not link:
                id_el = entry.find('{http://www.w3.org/2005/Atom}id')
                if id_el is not None and id_el.text:
                    link = id_el.text.strip()
                    
            # 著者一覧 (日本語著者名優先、なければ英語著者名)
            authors = []
            ja_authors = entry.findall('{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}ja/{http://www.w3.org/2005/Atom}name')
            for a in ja_authors:
                if a.text and a.text.strip():
                    authors.append(a.text.strip())
            if not authors:
                en_authors = entry.findall('{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}en/{http://www.w3.org/2005/Atom}name')
                for a in en_authors:
                    if a.text and a.text.strip():
                        authors.append(a.text.strip())
                        
            # 雑誌名 (資料名)
            journal = ""
            ja_mat_el = entry.find('{http://www.w3.org/2005/Atom}material_title/{http://www.w3.org/2005/Atom}ja')
            if ja_mat_el is not None and ja_mat_el.text:
                journal = ja_mat_el.text.strip()
            if not journal:
                en_mat_el = entry.find('{http://www.w3.org/2005/Atom}material_title/{http://www.w3.org/2005/Atom}en')
                if en_mat_el is not None and en_mat_el.text:
                    journal = en_mat_el.text.strip()
                    
            # 発行日・更新日
            pubdate = ""
            updated_el = entry.find('{http://www.w3.org/2005/Atom}updated')
            if updated_el is not None and updated_el.text:
                # 2025-11-10T09:00+09:00 -> 2025-11-10
                pubdate = updated_el.text.strip()[:10]
            if not pubdate:
                pubyear_el = entry.find('{http://www.w3.org/2005/Atom}pubyear')
                if pubyear_el is not None and pubyear_el.text:
                    pubdate = pubyear_el.text.strip()
                    
            # DOI
            doi = ""
            doi_el = entry.find('{http://prismstandard.org/namespaces/basic/2.0/}doi')
            if doi_el is not None and doi_el.text:
                doi = doi_el.text.strip()
                
            papers.append({
                "title": title,
                "authors": authors,
                "journal": journal or "J-STAGE 登載誌",
                "pubdate": pubdate,
                "url": link,
                "doi": doi or None,
                "source_api": "J-STAGE",
                "cited_by_count": 0,
                "matched_keywords": [keyword]
            })
            
        logger.info(f"J-STAGE: Fetched {len(papers)} papers for '{keyword}'")
    except Exception as e:
        logger.warning(f"J-STAGE: Failed to fetch papers for '{keyword}': {e}")
        
    return papers
