import urllib.request
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 厚生労働省公式新着RSS
MHLW_RSS_URLS = [
    "https://www.mhlw.go.jp/stf/news.rdf", # 厚生労働省 新着情報RSS 1.0
]

def fetch_mhlw_news(policy_keywords: List[str], days_back: int = 14) -> List[Dict[str, Any]]:
    """
    厚生労働省の新着RSSから、指定キーワードに該当する制度・診療報酬・医療ニュースを取得する。
    要約や転載は行わず、タイトル・日付・原文リンクのみを取得する。
    """
    news_items = []
    seen_urls = set()
    
    for rss_url in MHLW_RSS_URLS:
        req = urllib.request.Request(
            rss_url,
            headers={"User-Agent": "PT-Daily-Digest/1.0 (mailto:admin@example.com)"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                namespaces = {
                    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                    'rss': 'http://purl.org/rss/1.0/',
                    'dc': 'http://purl.org/dc/elements/1.1/'
                }
                
                items = root.findall('.//rss:item', namespaces)
                if not items:
                    items = root.findall('.//item')
                    
                for item in items:
                    title_elem = item.find('rss:title', namespaces) if item.find('rss:title', namespaces) is not None else item.find('title')
                    link_elem = item.find('rss:link', namespaces) if item.find('rss:link', namespaces) is not None else item.find('link')
                    date_elem = item.find('dc:date', namespaces) if item.find('dc:date', namespaces) is not None else item.find('date')
                    
                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                    date_str = date_elem.text.strip() if date_elem is not None and date_elem.text else ""
                    
                    if not title or not link or link in seen_urls:
                        continue
                        
                    # キーワード一致のチェック
                    title_lower = title.lower()
                    matched_kw = [kw for kw in policy_keywords if kw.lower() in title_lower or kw in title]
                    
                    if matched_kw:
                        seen_urls.add(link)
                        formatted_date = date_str[:10] if len(date_str) >= 10 else date_str
                        
                        news_items.append({
                            "title": title,
                            "url": link,
                            "pubdate": formatted_date,
                            "matched_keywords": matched_kw,
                            "source": "厚生労働省"
                        })
                        
        except Exception as e:
            logger.error(f"Error fetching RSS ({rss_url}): {e}")
            
    logger.info(f"Fetched {len(news_items)} MHLW policy news matching keywords.")
    return news_items
