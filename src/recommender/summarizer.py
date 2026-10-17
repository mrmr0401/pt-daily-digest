import os
import re
import json
import urllib.request
import urllib.error
import logging
import time
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def _parse_gemini_json_response(raw_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Geminiの出力から translated_title と summary を安全に抽出する"""
    text = raw_text.strip()
    # ```json ... ``` のコードブロックを除去
    if "```" in text:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            text = match.group(1).strip()
            
    try:
        data = json.loads(text)
        translated_title = data.get("translated_title", "").strip() or None
        summary = data.get("summary", "").strip() or None
        return translated_title, summary
    except Exception:
        pass
        
    # JSONパース失敗時の正規表現フォールバック
    trans_match = re.search(r'"translated_title"\s*:\s*"([^"]+)"', text)
    sum_match = re.search(r'"summary"\s*:\s*"([^"]+)"', text)
    
    translated_title = trans_match.group(1) if trans_match else None
    summary = sum_match.group(1) if sum_match else (text if len(text) < 300 else None)
    return translated_title, summary

def generate_gemini_summary_and_translation(title: str, item_type: str, meta_info: str, api_key: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Gemini 1.5 Flash API を呼び出し、
    - 英語論文: 日本語タイトル翻訳(translated_title) + 臨床的日本語要約(summary)
    - 制度ニュース: 日本語要約(summary)
    を生成する。
    失敗時やエラー時は例外を発生させず (None, None) を返す。
    """
    if not api_key:
        return None, None

    is_paper = item_type == "paper"

    if is_paper:
        prompt = (
            "あなたは理学療法士（PT）・リハビリテーション管理職のための専門アシスタントです。\n"
            "以下の【学術論文（英語）】について、次の2点を生成し、必ず指定のJSONフォーマットのみで出力してください。\n\n"
            "1. translated_title: 英語の論文タイトルを、理学療法士が直感的に理解しやすい自然で正確な日本語に翻訳したもの\n"
            "2. summary: 理学療法士にとっての臨床的示唆やリハビリテーション介入の要点を、2〜3文（80〜120文字程度）でわかりやすく要約したもの\n\n"
            f"【英語タイトル】: {title}\n"
            f"【補足情報】: {meta_info}\n\n"
            "【出力JSONフォーマット】 (マークダウンの```jsonや余計な解説は付けず、純粋なJSONのみ出力してください):\n"
            '{\n  "translated_title": "...",\n  "summary": "..."\n}'
        )
    else:
        prompt = (
            "あなたは理学療法士（PT）・リハビリテーション管理職のための専門アシスタントです。\n"
            "以下の【厚生労働省 制度・診療報酬ニュース】について、理学療法士にとっての制度上のポイントや医療・介護報酬における留意点を、"
            "日本語で2〜3文（80〜120文字程度）でわかりやすく要約し、指定のJSONフォーマットのみで出力してください。\n\n"
            f"【タイトル】: {title}\n"
            f"【補足情報】: {meta_info}\n\n"
            "【出力JSONフォーマット】:\n"
            '{\n  "translated_title": null,\n  "summary": "..."\n}'
        )

    request_data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 300
        }
    }

    url = f"{GEMINI_API_URL}?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(request_data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts and "text" in parts[0]:
                    raw_text = parts[0]["text"].strip()
                    return _parse_gemini_json_response(raw_text)
    except urllib.error.HTTPError as e:
        logger.warning(f"Gemini API HTTP Error ({e.code}): {e.reason}")
    except urllib.error.URLError as e:
        logger.warning(f"Gemini API URL Error: {e.reason}")
    except Exception as e:
        logger.warning(f"Gemini API unexpected error: {e}")
        
    return None, None

def attach_ai_summaries(items: List[Dict[str, Any]], api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    おすすめアイテム一覧に対して、Gemini APIによる日本語翻訳と日本語要約を付与する。
    APIキーが未設定の場合はスキップし、API失敗時も全体の処理を継続する。
    """
    resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
    
    if not resolved_api_key:
        logger.info("GEMINI_API_KEY is not set. Skipping AI summary and translation generation.")
        for item in items:
            item["translated_title"] = None
            item["ai_summary"] = None
        return items

    logger.info(f"Generating Gemini AI summaries & translations for {len(items)} recommended items...")
    
    for i, item in enumerate(items):
        title = item.get("title", "")
        item_type = item.get("item_type", "paper")
        
        meta_parts = []
        if item.get("journal"):
            meta_parts.append(f"掲載誌: {item.get('journal')}")
        if item.get("authors"):
            meta_parts.append(f"著者: {', '.join(item.get('authors')[:3])}")
        if item.get("matched_keywords"):
            meta_parts.append(f"関連分野: {', '.join(item.get('matched_keywords'))}")
        meta_info = " / ".join(meta_parts)
        
        try:
            trans_title, summary = generate_gemini_summary_and_translation(title, item_type, meta_info, resolved_api_key)
            item["translated_title"] = trans_title
            item["ai_summary"] = summary
            
            if trans_title or summary:
                logger.info(f"[{i+1}/{len(items)}] Success for: {title[:30]}... (Trans: {'Yes' if trans_title else 'No'}, Summary: {'Yes' if summary else 'No'})")
            else:
                logger.warning(f"[{i+1}/{len(items)}] Summary/translation was empty for: {title[:30]}...")
        except Exception as e:
            logger.warning(f"Failed to generate summary/translation for item {i}: {e}")
            item["translated_title"] = None
            item["ai_summary"] = None
            
        # 無料枠レートリミット配慮のための微小ウェイト
        if i < len(items) - 1:
            time.sleep(0.3)
            
    return items

