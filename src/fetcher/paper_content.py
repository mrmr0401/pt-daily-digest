import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import logging
import re
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

USER_AGENT = "PT-Daily-Digest/1.0 (mailto:admin@example.com)"

def restore_openalex_abstract(inverted_index: Optional[Dict[str, list]]) -> str:
    """OpenAlex の abstract_inverted_index から英語アブストラクト全文を復元する"""
    if not inverted_index:
        return ""
    pos_map = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            pos_map[pos] = word
    sorted_positions = sorted(pos_map.keys())
    return " ".join([pos_map[p] for p in sorted_positions]).strip()

def fetch_pmc_full_text(pmc_id: str) -> Optional[str]:
    """PubMed Central (PMC) BioC API からオープンアクセス論文の全文テキストを取得する"""
    clean_id = pmc_id.upper()
    if not clean_id.startswith("PMC"):
        clean_id = f"PMC{clean_id}"
        
    url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{clean_id}/unicode"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
            documents = data.get("documents", [])
            if not documents:
                return None
                
            passages = documents[0].get("passages", [])
            sections = []
            for p in passages:
                text = p.get("text", "").strip()
                infons = p.get("infons", {})
                sec_type = infons.get("section_type", "")
                if text:
                    if sec_type and sec_type not in ["TITLE", "ABSTRACT"]:
                        sections.append(f"\n--- {sec_type} ---\n{text}")
                    else:
                        sections.append(text)
                        
            full_text = "\n\n".join(sections).strip()
            if len(full_text) > 200:
                logger.info(f"Successfully fetched PMC full text for {clean_id} ({len(full_text)} chars).")
                return full_text
    except Exception as e:
        logger.debug(f"PMC BioC fetch failed for {clean_id}: {e}")
        
    return None

def fetch_pubmed_details(pmid: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    PubMed の論文から (full_text, abstract_text, is_oa) を取得する。
    1. PMCリンクがあればPMCから全文取得
    2. なければPubMed efetchから抄録全文を取得
    """
    if not pmid:
        return None, None, False
        
    # 1. PMCリンクの確認
    pmc_id = None
    elink_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id={pmid}&cmd=neighbor&linkname=pubmed_pmc&retmode=json"
    req_elink = urllib.request.Request(elink_url, headers={"User-Agent": USER_AGENT})
    
    try:
        with urllib.request.urlopen(req_elink, timeout=8) as res:
            data = json.loads(res.read().decode("utf-8"))
            linkset = data.get("linksets", [{}])[0]
            linksetdbs = linkset.get("linksetdbs", [])
            for ldb in linksetdbs:
                if ldb.get("linkname") == "pubmed_pmc":
                    links = ldb.get("links", [])
                    if links:
                        pmc_id = str(links[0])
                        break
    except Exception as e:
        logger.debug(f"PubMed elink check error ({pmid}): {e}")

    if pmc_id:
        full_text = fetch_pmc_full_text(pmc_id)
        if full_text:
            return full_text, None, True

    # 2. 全文がない場合は PubMed efetch XML で Abstract を取得
    efetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
    req_efetch = urllib.request.Request(efetch_url, headers={"User-Agent": USER_AGENT})
    
    try:
        with urllib.request.urlopen(req_efetch, timeout=10) as res:
            xml_data = res.read()
            root = ET.fromstring(xml_data)
            abstract_elems = root.findall(".//AbstractText")
            if abstract_elems:
                texts = []
                for elem in abstract_elems:
                    label = elem.attrib.get("Label")
                    txt = elem.text.strip() if elem.text else ""
                    if label:
                        texts.append(f"{label}: {txt}")
                    elif txt:
                        texts.append(txt)
                abstract_text = "\n\n".join(texts).strip()
                if abstract_text:
                    logger.info(f"Fetched PubMed abstract for PMID {pmid} ({len(abstract_text)} chars).")
                    return None, abstract_text, False
    except Exception as e:
        logger.warning(f"PubMed efetch abstract error ({pmid}): {e}")

    return None, None, False

def fetch_openalex_details(openalex_id_or_url: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    OpenAlex API から (full_text, abstract_text, is_oa) を取得する。
    """
    if not openalex_id_or_url:
        return None, None, False
        
    work_id = openalex_id_or_url.replace("https://openalex.org/", "").strip()
    url = f"https://api.openalex.org/works/{work_id}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            
            # オープンアクセス判定
            oa_info = data.get("open_access", {})
            is_oa = bool(oa_info.get("is_oa", False))
            
            # PMC ID があれば全文取得を試みる
            pmcid = data.get("ids", {}).get("pmcid")
            if pmcid:
                clean_pmcid = pmcid.replace("https://www.ncbi.nlm.nih.gov/pmc/articles/", "").strip("/")
                full_text = fetch_pmc_full_text(clean_pmcid)
                if full_text:
                    return full_text, None, True
                    
            # アブストラクトの復元
            inverted_index = data.get("abstract_inverted_index")
            abstract_text = restore_openalex_abstract(inverted_index)
            if abstract_text:
                logger.info(f"Restored OpenAlex abstract for {work_id} ({len(abstract_text)} chars).")
                return None, abstract_text, is_oa
    except Exception as e:
        logger.warning(f"OpenAlex details error ({work_id}): {e}")

    return None, None, False

def enrich_paper_content(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    1件の論文に対して、全文テキストまたはアブストラクトテキスト、およびOA判定を付与する。
    """
    pmid = paper.get("pmid")
    openalex_id = paper.get("openalex_id")
    
    full_text = None
    abstract_text = None
    is_oa = False
    
    if pmid:
        full_text, abstract_text, is_oa = fetch_pubmed_details(pmid)
        
    if not full_text and not abstract_text and openalex_id:
        full_text, abstract_text, is_oa = fetch_openalex_details(openalex_id)
        
    paper["full_text"] = full_text
    paper["abstract_text"] = abstract_text
    paper["is_oa"] = is_oa
    paper["content_type"] = "full_text" if full_text else ("abstract" if abstract_text else "title_only")
    
    return paper
