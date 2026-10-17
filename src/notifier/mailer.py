import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

SITE_URL = "https://mrmr0401.github.io/pt-daily-digest/"

def _build_html_email(recommended: List[Dict[str, Any]], policy_news: List[Dict[str, Any]], papers: List[Dict[str, Any]], today_date: str) -> str:
    """スマートフォンで見やすいインラインスタイルのHTMLメール本文を生成する"""
    
    # おすすめ5件のHTMLカード生成
    rec_cards_html = ""
    for i, item in enumerate(recommended):
        rank = i + 1
        rank_bg = "#f59e0b" if rank == 1 else ("#94a3b8" if rank == 2 else ("#b45309" if rank == 3 else "#0284c7"))
        
        is_policy = item.get("item_type") == "policy"
        type_badge = '<span style="background-color:#d97706; color:#ffffff; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:4px;">厚生労働省</span>' if is_policy else f'<span style="background-color:#0369a1; color:#ffffff; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:4px;">{item.get("source_api", "論文")}</span>'
        
        score_val = item.get("total_score", 0)
        
        # タイトル & 翻訳タイトル
        trans_title = item.get("translated_title")
        orig_title = item.get("title", "")
        item_url = item.get("url", "#")
        
        if trans_title:
            title_block = f'''
            <div style="font-size:15px; font-weight:bold; line-height:1.4; margin:6px 0 2px;">
                <a href="{item_url}" target="_blank" style="color:#0284c7; text-decoration:none;">{trans_title}</a>
            </div>
            <div style="font-size:12px; color:#64748b; font-style:italic; margin-bottom:6px;">
                原題: {orig_title}
            </div>
            '''
        else:
            title_block = f'''
            <div style="font-size:15px; font-weight:bold; line-height:1.4; margin:6px 0 6px;">
                <a href="{item_url}" target="_blank" style="color:#0284c7; text-decoration:none;">{orig_title}</a>
            </div>
            '''
            
        # 著者・雑誌情報
        authors = item.get("authors", [])
        authors_str = ", ".join(authors[:2]) + ("..." if len(authors) > 2 else "")
        meta_html = ""
        if not is_policy and (authors_str or item.get("journal")):
            meta_html = f'''
            <div style="font-size:12px; color:#64748b; margin-bottom:8px;">
                {f"<span>著者: {authors_str}</span> | " if authors_str else ""}{f"<span>掲載誌: <em>{item.get('journal')}</em></span>" if item.get('journal') else ""}
            </div>
            '''
            
        # AI要約ブロック
        ai_summary = item.get("ai_summary")
        summary_html = ""
        if ai_summary:
            disclaimer = "⚠️ AI要約・翻訳のため原文で確認してください" if trans_title else "⚠️ AI要約のため原文で確認してください"
            summary_html = f'''
            <div style="background-color:#f5f3ff; border:1px solid #ddd6fe; border-left:3px solid #8b5cf6; padding:10px; border-radius:6px; margin:8px 0;">
                <div style="font-size:11px; font-weight:bold; color:#7c3aed; margin-bottom:4px;">🤖 AIによる要約 (Gemini)</div>
                <div style="font-size:13px; color:#1e1b4b; line-height:1.5; margin-bottom:6px;">{ai_summary}</div>
                <div style="font-size:10px; color:#b45309; background-color:#fef3c7; padding:2px 6px; border-radius:3px; display:inline-block;">{disclaimer}</div>
            </div>
            '''
            
        rec_cards_html += f'''
        <div style="background-color:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:12px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
                <div>
                    <span style="background-color:{rank_bg}; color:#ffffff; font-size:11px; font-weight:bold; padding:2px 6px; border-radius:4px;">#{rank}</span>
                    {type_badge}
                    <span style="font-size:11px; color:#b45309; font-weight:bold; margin-left:4px;">⭐ {score_val}pt</span>
                </div>
                <span style="font-size:11px; color:#94a3b8;">{item.get("pubdate", "")}</span>
            </div>
            {title_block}
            {meta_html}
            {summary_html}
            <div style="text-align:right; margin-top:8px;">
                <a href="{item_url}" target="_blank" style="display:inline-block; font-size:12px; font-weight:bold; color:#0284c7; background-color:#e0f2fe; padding:4px 10px; border-radius:4px; text-decoration:none;">原文を見る ↗</a>
            </div>
        </div>
        '''

    # 厚労省新着ハイライト (最大3件)
    policy_list_html = ""
    for p in policy_news[:3]:
        policy_list_html += f'''
        <li style="margin-bottom:6px; font-size:13px; line-height:1.4;">
            <a href="{p.get('url', '#')}" target="_blank" style="color:#0f172a; text-decoration:none;">{p.get('title', '')}</a>
            <span style="font-size:11px; color:#64748b;">({p.get('pubdate', '')})</span>
        </li>
        '''

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PT Daily Digest</title>
</head>
<body style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color:#f8fafc; color:#0f172a; margin:0; padding:16px 8px; line-height:1.6;">
    <div style="max-width:600px; margin:0 auto; background-color:#ffffff; border-radius:12px; overflow:hidden; border:1px solid #e2e8f0;">
        
        <!-- ヘッダー -->
        <div style="background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color:#ffffff; padding:20px 16px; text-align:center;">
            <div style="font-size:20px; font-weight:bold; color:#f8fafc;">📋 PT Daily Digest</div>
            <div style="font-size:12px; color:#94a3b8; margin-top:4px;">理学療法士管理職向け情報ダイジェスト | {today_date}</div>
        </div>

        <!-- コンテンツ本体 -->
        <div style="padding:16px;">
            
            <!-- 今日の注目おすすめ 5選 -->
            <div style="background-color:#fffbeb; border:1px solid #fef3c7; border-radius:8px; padding:12px; margin-bottom:20px;">
                <div style="font-size:16px; font-weight:bold; color:#b45309; margin-bottom:2px;">🌟 本日の注目おすすめ 5選</div>
                <div style="font-size:11px; color:#78350f; margin-bottom:12px;">重要キーワード一致・最新度・被引用数より厳選（Gemini翻訳・要約付き）</div>
                {rec_cards_html}
            </div>

            <!-- 厚労省新着ハイライト -->
            <div style="margin-bottom:20px;">
                <div style="font-size:14px; font-weight:bold; color:#0f172a; border-bottom:2px solid #f59e0b; padding-bottom:4px; margin-bottom:10px;">
                    🏛️ 厚生労働省 新着情報 ({len(policy_news)}件中 最新3件)
                </div>
                <ul style="padding-left:18px; margin:0;">
                    {policy_list_html}
                </ul>
            </div>

            <!-- Webサイト案内ボタン -->
            <div style="text-align:center; padding:16px 0;">
                <a href="{SITE_URL}" target="_blank" style="display:inline-block; background:linear-gradient(90deg, #f59e0b, #0284c7); color:#ffffff; font-size:14px; font-weight:bold; padding:10px 24px; border-radius:24px; text-decoration:none; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                    📱 Webページで全件 ({len(papers)}件の論文) を確認する
                </a>
            </div>

        </div>

        <!-- フッター -->
        <div style="background-color:#f1f5f9; padding:14px; text-align:center; font-size:11px; color:#64748b; border-top:1px solid #e2e8f0;">
            <p style="margin:0 0 4px;">PT Daily Digest &copy; {datetime.now().year} | 毎朝自動配信</p>
            <p style="margin:0;"><a href="{SITE_URL}" style="color:#0284c7;">Web版を開く</a></p>
        </div>

    </div>
</body>
</html>
'''
    return html

def _build_text_email(recommended: List[Dict[str, Any]], policy_news: List[Dict[str, Any]], papers: List[Dict[str, Any]], today_date: str) -> str:
    """プレーンテキストメール本文"""
    lines = [
        f"=== 📋 PT Daily Digest ({today_date}) ===",
        "理学療法士管理職向け情報ダイジェスト",
        f"Web版: {SITE_URL}",
        "",
        "-----------------------------------------",
        "🌟 本日の注目おすすめ 5選",
        "-----------------------------------------"
    ]
    
    for i, item in enumerate(recommended):
        rank = i + 1
        trans_title = item.get("translated_title")
        orig_title = item.get("title", "")
        
        lines.append(f"【#{rank}】 {trans_title if trans_title else orig_title}")
        if trans_title:
            lines.append(f"原題: {orig_title}")
            
        if item.get("ai_summary"):
            lines.append(f"🤖 要約: {item.get('ai_summary')}")
            lines.append("※AI要約・翻訳のため原文でご確認ください。")
            
        lines.append(f"URL: {item.get('url', '')}")
        lines.append("")
        
    lines.append("-----------------------------------------")
    lines.append(f"🏛️ 厚生労働省 新着ニュース: 全{len(policy_news)}件")
    lines.append(f"📚 学術論文 (PubMed/OpenAlex): 全{len(papers)}件")
    lines.append("-----------------------------------------")
    lines.append(f"詳細・全件検索はWebページをご覧ください: {SITE_URL}")
    
    return "\n".join(lines)

def send_digest_email(
    recommended: List[Dict[str, Any]], 
    policy_news: List[Dict[str, Any]], 
    papers: List[Dict[str, Any]]
) -> bool:
    """
    環境変数 (MAIL_TO, SMTP_USER, SMTP_PASSWORD 等) を確認し、
    設定されている場合にダイジェストメールを送信する。
    未設定時やエラー発生時も例外は投げず安全にスキップする。
    """
    mail_to = os.environ.get("MAIL_TO", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port_str = os.environ.get("SMTP_PORT", "587").strip()
    
    if not mail_to or not smtp_user or not smtp_password:
        logger.info("Mail delivery skipped: MAIL_TO, SMTP_USER, or SMTP_PASSWORD is not configured.")
        return False
        
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 587
        
    today_date = datetime.now().strftime("%Y年%m月%d日")
    subject = f"【PT Daily Digest】今日のおすすめ5選 & 新着情報 ({today_date})"
    
    # 複数アドレスの分割 (カンマ区切り対応)
    recipients = [addr.strip() for addr in mail_to.split(",") if addr.strip()]
    if not recipients:
        logger.info("No valid recipient email address found.")
        return False
        
    logger.info(f"Preparing digest email to: {recipients} via {smtp_host}:{smtp_port}...")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"PT Daily Digest <{smtp_user}>"
    msg["To"] = ", ".join(recipients)
    
    text_content = _build_text_email(recommended, policy_news, papers, today_date)
    html_content = _build_html_email(recommended, policy_news, papers, today_date)
    
    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    
    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipients, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipients, msg.as_string())
                
        logger.info(f"Successfully sent digest email to {len(recipients)} recipient(s).")
        return True
    except Exception as e:
        logger.warning(f"Failed to send digest email: {e}")
        return False
