import os
import re
import json
import logging
import urllib.request
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

CACHE_FILE_PATH = os.path.join("data", "keyword_cache.json")

def is_japanese(text: str) -> bool:
    """ひらがな・カタカナ・漢字を含むかどうかを判定する"""
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))

def load_keyword_cache() -> Dict[str, List[str]]:
    """data/keyword_cache.json から翻訳キャッシュを読み込む"""
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load keyword cache: {e}")
    return {}

def save_keyword_cache(cache: Dict[str, List[str]]) -> None:
    """data/keyword_cache.json に翻訳キャッシュを保存する"""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
        with open(CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save keyword cache: {e}")

def translate_keyword_with_gemini(japanese_keyword: str) -> List[str]:
    """
    Gemini API (無料枠) を用いて、医学・リハビリ文献検索向け英語キーワード (MeSH用語等を意識) に翻訳する。
    最大2候補を返す。APIキー未設定または失敗時は空リストを返し、処理を継続する。
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info(f"GEMINI_API_KEY not set. Skipping AI translation for '{japanese_keyword}'.")
        return []

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = (
        f"あなたは医学・理学療法・リハビリテーション分野の学術翻訳の専門家です。\n"
        f"以下の日本語キーワードを、PubMed等の医学文献データベースでの検索に最適な標準的英語医学用語（MeSH用語等を意識した同義語）に翻訳してください。\n"
        f"最も一般的かつ適切な英語表現を、最大2つまでカンマ区切りで出力してください。\n"
        f"解説、記号、余分な挨拶は一切含めず、英語キーワードのみを出力してください。\n\n"
        f"日本語キーワード: {japanese_keyword}"
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 60
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                # カンマ区切りで分割し、クリーンアップ
                terms = [t.strip().strip('"').strip("'").lower() for t in text.split(",") if t.strip()]
                # 最大2候補
                valid_terms = [t for t in terms if t and not is_japanese(t)][:2]
                if valid_terms:
                    logger.info(f"Gemini translated '{japanese_keyword}' -> {valid_terms}")
                    return valid_terms
    except Exception as e:
        logger.warning(f"Gemini translation failed for '{japanese_keyword}': {e}")

    return []

def get_english_keywords(japanese_keyword: str, manual_translations: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """
    日本語キーワードに対応する英語キーワード候補を取得する。
    優先度:
    1. 手動辞書 (config.yaml の keyword_translations)
    2. data/keyword_cache.json のキャッシュ
    3. Gemini API (無料枠) による自動翻訳 (取得後はキャッシュに保存)
    """
    clean_kw = japanese_keyword.strip()
    if not is_japanese(clean_kw):
        return [clean_kw]

    # 1. 手動辞書の確認
    if manual_translations and clean_kw in manual_translations:
        candidates = manual_translations[clean_kw]
        if isinstance(candidates, str):
            candidates = [candidates]
        logger.info(f"Using manual translation for '{clean_kw}': {candidates}")
        return candidates

    # 2. ローカルキャッシュの確認
    cache = load_keyword_cache()
    if clean_kw in cache and cache[clean_kw]:
        logger.info(f"Using cached translation for '{clean_kw}': {cache[clean_kw]}")
        return cache[clean_kw]

    # 3. Gemini API での翻訳
    candidates = translate_keyword_with_gemini(clean_kw)
    if candidates:
        cache[clean_kw] = candidates
        save_keyword_cache(cache)
        return candidates

    # 翻訳できない場合は空リストを返す
    return []
