import os
import json
import urllib.request
import urllib.error
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def generate_detailed_report(item: Dict[str, Any], api_key: Optional[str] = None) -> str:
    """
    1件のアイテム（論文または制度ニュース）に対して、Gemini 1.5 Flash を用いて
    詳細な日本語翻訳・臨床解説レポート（PDF掲載用）を生成する。
    APIキー未設定やAPI失敗時もエラーを出さず、フォールバックの構造化レポートを返す。
    """
    resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
    item_type = item.get("item_type", "paper")
    title = item.get("title", "")
    trans_title = item.get("translated_title") or title
    authors = ", ".join(item.get("authors", [])[:5]) or "情報なし"
    journal = item.get("journal", "掲載誌不明")
    pubdate = item.get("pubdate", "日付不明")
    doi = item.get("doi", "")
    url = item.get("url", "#")
    is_oa = item.get("is_oa", False)
    content_type = item.get("content_type", "title_only")
    
    full_text = item.get("full_text")
    abstract_text = item.get("abstract_text")

    # APIキーがない場合のフォールバックレポート
    if not resolved_api_key:
        return _build_fallback_report(item)

    if item_type == "paper":
        if full_text:
            # オープンアクセス全文がある場合
            target_text = full_text[:12000] # 入力トークン上限に余裕を持たせる
            prompt = (
                "あなたは理学療法士（PT）・リハビリテーション医療管理職のための専門アシスタントです。\n"
                "以下のオープンアクセス学術論文の全文を読み、臨床現場の理学療法士が深く理解・実践できるよう、"
                "詳細な日本語翻訳・臨床解説レポートを作成してください。\n\n"
                f"【論文原題】: {title}\n"
                f"【日本語訳題】: {trans_title}\n"
                f"【著者】: {authors}\n"
                f"【掲載誌】: {journal} ({pubdate})\n\n"
                f"【論文本文テキスト】:\n{target_text}\n\n"
                "以下の見出し構成（Markdown形式）で、わかりやすく詳細に記述してください：\n"
                "## 1. 構造化アブストラクトの日本語訳\n"
                "（背景、方法、結果、結論）\n\n"
                "## 2. 研究の背景と目的\n"
                "（臨床における課題と本研究の狙い）\n\n"
                "## 3. 対象と理学療法介入プロトコル\n"
                "（被験者・疾患情報、具体的なリハビリ介入内容・頻度・評価指標）\n\n"
                "## 4. 主な結果と統計的知見\n"
                "（主要評価項目、数値データ、有意差の有無）\n\n"
                "## 5. 考察と理学療法への臨床的示唆\n"
                "（臨床現場でどう活かせるか、患者への適用時の留意点、今後の展望）\n\n"
                "※本文のみを出力してください。"
            )
        elif abstract_text:
            # アブストラクトのみの場合 (有料論文・抄録公開論文)
            prompt = (
                "あなたは理学療法士（PT）・リハビリテーション医療管理職のための専門アシスタントです。\n"
                "以下の学術論文のアブストラクト（抄録全文）を読み、理学療法士のための詳細な日本語翻訳・臨床解説レポートを作成してください。\n\n"
                f"【論文原題】: {title}\n"
                f"【日本語訳題】: {trans_title}\n"
                f"【著者】: {authors}\n"
                f"【掲載誌】: {journal} ({pubdate})\n\n"
                f"【英語アブストラクト全文】:\n{abstract_text}\n\n"
                "以下の見出し構成（Markdown形式）で、わかりやすく詳細に記述してください：\n"
                "## 1. アブストラクトの完全日本語翻訳\n"
                "（英文アブストラクトの自然で正確な全文翻訳）\n\n"
                "## 2. 研究の背景と臨床的意義\n"
                "（本研究が対象とする病態や課題）\n\n"
                "## 3. 研究手法と評価項目\n"
                "（デザイン、介入・測定項目）\n\n"
                "## 4. 報告された主要な結果\n"
                "（アブストラクトに記載された結果と数値）\n\n"
                "## 5. 理学療法士のための臨床的活用ポイント\n"
                "（臨床推論や介入方針における示唆と留意事項）\n\n"
                "※本文のみを出力してください。"
            )
        else:
            # タイトル・メタ情報のみの場合
            prompt = (
                "あなたは理学療法士（PT）・リハビリテーション医療管理職のための専門アシスタントです。\n"
                f"以下の学術論文情報から、理学療法士向けの解説レポートを作成してください。\n\n"
                f"【論文原題】: {title}\n"
                f"【日本語訳題】: {trans_title}\n"
                f"【著者】: {authors}\n"
                f"【掲載誌】: {journal} ({pubdate})\n\n"
                "以下の構成で記述してください：\n"
                "## 1. 論文の概要と注目ポイント\n"
                "## 2. 理学療法領域における関連性と臨床的示唆\n"
            )
    else:
        # 厚生労働省 制度・診療報酬ニュースの場合
        prompt = (
            "あなたは理学療法士（PT）・リハビリテーション医療管理職のための専門アシスタントです。\n"
            "以下の厚生労働省の公式通知・制度ニュースについて、理学療法部門の管理職向けの詳細な実務解説レポートを作成してください。\n\n"
            f"【通知タイトル】: {title}\n"
            f"【公表日】: {pubdate}\n"
            f"【関連キーワード】: {', '.join(item.get('matched_keywords', []))}\n\n"
            "以下の見出し構成（Markdown形式）で記述してください：\n"
            "## 1. 通知・改定の概要\n"
            "## 2. 診療報酬・介護報酬・医療制度上の要点\n"
            "## 3. リハビリテーション部門・管理職における実務対応と留意事項\n"
        )

    request_data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
    }

    url = f"{GEMINI_API_URL}?key={resolved_api_key}"
    headers = {"Content-Type": "application/json"}

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(request_data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    report_text = parts[0]["text"].strip()
                    logger.info(f"Generated detailed report for: {title[:30]}...")
                    return report_text
    except Exception as e:
        logger.warning(f"Gemini API report generation failed: {e}")

    return _build_fallback_report(item)

def _build_fallback_report(item: Dict[str, Any]) -> str:
    """API未設定・失敗時の構造化レポート"""
    trans_title = item.get("translated_title") or item.get("title", "")
    abstract = item.get("abstract_text", "")
    summary = item.get("ai_summary", "要約情報は未取得です。")
    is_oa = item.get("is_oa", False)
    
    sections = [
        f"## 1. 論文・ニュース概要\n\n{summary}\n",
        f"## 2. 公開ステータス\n\n- オープンアクセス区分: {'オープンアクセス (全文閲覧可能)' if is_oa else '有料購読・抄録公開'}\n- 掲載誌: {item.get('journal', '情報なし')}\n- 出版日: {item.get('pubdate', '情報なし')}\n"
    ]
    if abstract:
        sections.append(f"## 3. 英文アブストラクト (原文抄録)\n\n{abstract}\n")
    sections.append("## 4. 原文確認のご案内\n\n研究の詳細データや査読全文については、必ず上記原文URLよりご確認ください。\n")
    return "\n".join(sections)
