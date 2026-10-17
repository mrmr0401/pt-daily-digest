import os
import json
import urllib.request
import urllib.error
import logging
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def generate_gemini_summary(title: str, item_type: str, meta_info: str, api_key: str) -> Optional[str]:
    """
    Gemini 1.5 Flash API を呼び出し、理学療法士向けの簡潔な日本語要約（80〜120文字程度）を生成する。
    失敗時やエラー時は例外を発生させず None を返す。
    """
    if not api_key:
        return None

    type_label = "学術論文" if item_type == "paper" else "厚生労働省 制度・診療報酬ニュース"
    prompt = (
        f"あなたは理学療法士（PT）・リハビリテーション管理職のための専門アシスタントです。\n"
        f"以下の{type_label}について、理学療法士にとっての臨床的示唆や制度上の要点を、"
        f"日本語で簡潔に2〜3文（80〜120文字程度）でわかりやすく要約してください。\n\n"
        f"【タイトル】: {title}\n"
        f"【補足情報】: {meta_info}\n\n"
        f"※挨拶や前置き、鉤括弧は不要です。要約本文のみを出力してください。"
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
            "temperature": 0.3,
            "maxOutputTokens": 200
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
                    summary_text = parts[0]["text"].strip()
                    return summary_text
    except urllib.error.HTTPError as e:
        logger.warning(f"Gemini API HTTP Error ({e.code}): {e.reason}")
    except urllib.error.URLError as e:
        logger.warning(f"Gemini API URL Error: {e.reason}")
    except Exception as e:
        logger.warning(f"Gemini API unexpected error: {e}")
        
    return None

def attach_ai_summaries(items: List[Dict[str, Any]], api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    おすすめアイテム一覧に対して、Gemini APIによる日本語要約を付与する。
    APIキーが未設定の場合はスキップし、API失敗時も全体の処理を継続する。
    """
    resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
    
    if not resolved_api_key:
        logger.info("GEMINI_API_KEY is not set. Skipping AI summary generation.")
        for item in items:
            item["ai_summary"] = None
        return items

    logger.info(f"Generating Gemini AI summaries for {len(items)} recommended items...")
    
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
            summary = generate_gemini_summary(title, item_type, meta_info, resolved_api_key)
            item["ai_summary"] = summary
            if summary:
                logger.info(f"[{i+1}/{len(items)}] Summary generated for: {title[:30]}...")
            else:
                logger.warning(f"[{i+1}/{len(items)}] Summary was empty/failed for: {title[:30]}...")
        except Exception as e:
            logger.warning(f"Failed to generate summary for item {i}: {e}")
            item["ai_summary"] = None
            
        # 無料枠レートリミット配慮のための微小ウェイト
        if i < len(items) - 1:
            time.sleep(0.3)
            
    return items
