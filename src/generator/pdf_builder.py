import os
import re
from datetime import datetime
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

from src.generator.font_manager import register_japanese_fonts

class NumberedCanvas(canvas.Canvas):
    """2パスで総ページ数を計算し、各ページの下部に 'Page X / Y' を描画するキャンバス"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("JapaneseGothic", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # ヘッダー (上部)
        self.drawString(42, 800, "📋 PT Daily Digest - 理学療法士管理職向け学術レポート")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(42, 792, 553, 792)

        # フッター (下部)
        self.line(42, 45, 553, 45)
        today_str = datetime.now().strftime("%Y年%m月%d日")
        self.drawString(42, 32, f"発行日: {today_str} | Web版: https://mrmr0401.github.io/pt-daily-digest/")
        page_str = f"Page {self._pageNumber} / {page_count}"
        self.drawRightString(553, 32, page_str)
        self.restoreState()

def _get_pdf_styles(font_name: str):
    """日本語フォントを適用した ReportLab スタイルシートを取得する"""
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
        keepWithNext=True
    )

    orig_title_style = ParagraphStyle(
        'OrigTitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10,
        keepWithNext=True
    )

    heading_style = ParagraphStyle(
        'SecHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#0284c7"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyJP',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=14.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )

    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#92400e")
    )

    return title_style, orig_title_style, heading_style, body_style, meta_style, disclaimer_style

def _format_markdown_to_flowables(report_text: str, heading_style, body_style) -> list:
    """Markdownの見出しと段落を ReportLab の Flowables に変換する"""
    flowables = []
    lines = report_text.splitlines()
    
    current_para = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_para:
                text = " ".join(current_para).replace("<", "&lt;").replace(">", "&gt;")
                flowables.append(Paragraph(text, body_style))
                current_para = []
            continue
            
        if stripped.startswith("## ") or stripped.startswith("### "):
            if current_para:
                text = " ".join(current_para).replace("<", "&lt;").replace(">", "&gt;")
                flowables.append(Paragraph(text, body_style))
                current_para = []
            heading_text = stripped.lstrip("#").strip().replace("<", "&lt;").replace(">", "&gt;")
            flowables.append(Paragraph(f"<b>{heading_text}</b>", heading_style))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = stripped[2:].replace("<", "&lt;").replace(">", "&gt;")
            flowables.append(Paragraph(f"• {bullet_text}", body_style))
        else:
            current_para.append(stripped)
            
    if current_para:
        text = " ".join(current_para).replace("<", "&lt;").replace(">", "&gt;")
        flowables.append(Paragraph(text, body_style))
        
    return flowables

def _create_paper_flowables(item: Dict[str, Any], rank: int, styles_tuple) -> list:
    """1件の論文の要素一覧 (ヘッダー、メタ表、本文、注記) を組み立てる"""
    title_style, orig_title_style, heading_style, body_style, meta_style, disclaimer_style = styles_tuple
    
    flowables = []
    
    trans_title = item.get("translated_title") or item.get("title", "")
    orig_title = item.get("title", "")
    authors = ", ".join(item.get("authors", [])[:4]) or "情報なし"
    journal = item.get("journal", "掲載誌不明")
    pubdate = item.get("pubdate", "")
    doi = item.get("doi", "")
    url = item.get("url", "#")
    is_oa = item.get("is_oa", False)
    item_type = item.get("item_type", "paper")
    
    # 順位バッジ + 日本語タイトル
    type_label = "【学術論文】" if item_type == "paper" else "【厚労省通知】"
    flowables.append(Paragraph(f"<b>#{rank} {type_label} {trans_title}</b>", title_style))
    
    # 英語原題 (翻訳タイトルがある場合)
    if trans_title != orig_title:
        flowables.append(Paragraph(f"原題: <i>{orig_title}</i>", orig_title_style))
        
    # メタ情報テーブル
    oa_badge = "オープンアクセス (全文確認可)" if is_oa else "抄録公開"
    meta_data = [
        [Paragraph(f"<b>著者:</b> {authors}", meta_style), Paragraph(f"<b>掲載誌:</b> {journal} ({pubdate})", meta_style)],
        [Paragraph(f"<b>DOI:</b> {doi if doi else 'なし'}", meta_style), Paragraph(f"<b>区分:</b> {oa_badge}", meta_style)]
    ]
    t = Table(meta_data, colWidths=[255, 255])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    flowables.append(t)
    flowables.append(Spacer(1, 10))
    
    # 詳細レポート本文
    report_text = item.get("detailed_report", "")
    if report_text:
        content_flowables = _format_markdown_to_flowables(report_text, heading_style, body_style)
        flowables.extend(content_flowables)
    else:
        summary = item.get("ai_summary", "要約情報がありません。")
        flowables.append(Paragraph("<b>概要:</b>", heading_style))
        flowables.append(Paragraph(summary, body_style))
        
    flowables.append(Spacer(1, 8))
    
    # 免責事項・原文リンク枠
    disclaimer_text = (
        f"⚠️ 本レポートはAI (Gemini) による日本語翻訳・解説です。臨床判断・引用の際は必ず原文をご確認ください。<br/>"
        f"原文URL: <font color='#0284c7'><u>{url}</u></font>"
    )
    disc_table = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[510])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#fcd34d")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    flowables.append(disc_table)
    flowables.append(Spacer(1, 14))
    
    return flowables

def generate_single_pdf(item: Dict[str, Any], rank: int, output_pdf_path: str):
    """1件の個別PDFを生成する"""
    font_name = register_japanese_fonts()
    styles_tuple = _get_pdf_styles(font_name)
    
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=54,
        bottomMargin=54
    )
    
    flowables = _create_paper_flowables(item, rank, styles_tuple)
    doc.build(flowables, canvasmaker=NumberedCanvas)

def generate_combined_pdf(items: List[Dict[str, Any]], output_pdf_path: str):
    """おすすめ5件をまとめた総合PDFを生成する"""
    font_name = register_japanese_fonts()
    styles_tuple = _get_pdf_styles(font_name)
    
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=54,
        bottomMargin=54
    )
    
    all_flowables = []
    
    # 総合PDF用の表紙的見出し
    today_str = datetime.now().strftime("%Y年%m月%d日")
    cover_style = ParagraphStyle(
        'CoverTitle',
        parent=styles_tuple[0],
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=1, # 中央揃え
        spaceAfter=6
    )
    cover_sub = ParagraphStyle(
        'CoverSub',
        parent=styles_tuple[1],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceAfter=18
    )
    all_flowables.append(Paragraph("📋 PT Daily Digest - 本日の注目トピック 5選 (日本語全文レポート)", cover_style))
    all_flowables.append(Paragraph(f"発行日: {today_str} | 理学療法士管理職向け学術・制度ダイジェスト", cover_sub))
    all_flowables.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=14))
    
    for i, item in enumerate(items):
        rank = i + 1
        flowables = _create_paper_flowables(item, rank, styles_tuple)
        all_flowables.extend(flowables)
        if rank < len(items):
            all_flowables.append(PageBreak())
            
    doc.build(all_flowables, canvasmaker=NumberedCanvas)
