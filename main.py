import os
import logging
from src.utils.config import load_config
from src.fetcher.aggregator import fetch_all_papers
from src.fetcher.mhlw_news import fetch_mhlw_news
from src.fetcher.paper_content import enrich_paper_content
from src.recommender.scoring import select_top_recommendations
from src.recommender.summarizer import attach_ai_summaries
from src.recommender.full_translator import generate_detailed_report
from src.generator.pdf_builder import generate_single_pdf, generate_combined_pdf
from src.generator.html_builder import generate_docs
from src.notifier.mailer import send_digest_email

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== PT Daily Digest: Processing Started ===")
    
    # 1. 設定情報の読み込み
    config = load_config()
    keywords = config.get("keywords", ["stroke rehabilitation", "frailty", "physical therapy"])
    policy_keywords = config.get("policy_keywords", ["リハビリ", "診療報酬", "疑義解釈", "理学療法"])
    days_back = config.get("days_back", 14)
    max_results = config.get("max_results_per_keyword", 20)
    
    # 2. 制度・診療報酬関連ニュースの取得 (厚生労働省 RSS 等)
    logger.info("Fetching policy & healthcare news (MHLW)...")
    policy_news = fetch_mhlw_news(policy_keywords=policy_keywords, days_back=days_back)
    
    # 3. 学術論文データの取得 & 重複排除 (PubMed & OpenAlex)
    logger.info("Fetching research papers...")
    papers = fetch_all_papers(keywords=keywords, days_back=7, max_per_keyword=max_results)
    
    # 4. 「今日のおすすめ5件」の選定 & Gemini AI要約・タイトル翻訳の付加
    logger.info("Selecting Top 5 Recommendations...")
    recommended = select_top_recommendations(papers=papers, policy_news=policy_news, config=config, top_n=5)
    logger.info("Checking and generating AI summaries & translations for recommendations...")
    recommended = attach_ai_summaries(recommended)
    
    # 5. おすすめ5件の全文/抄録取得・詳細翻訳レポート生成・PDF生成
    logger.info("Enriching paper content, generating detailed reports and PDFs...")
    pdf_dir = os.path.join("docs", "pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    
    for i, item in enumerate(recommended):
        rank = i + 1
        if item.get("item_type") == "paper":
            enrich_paper_content(item)
            
        # 詳細レポートの生成 (Gemini)
        report_text = generate_detailed_report(item)
        item["detailed_report"] = report_text
        
        # 個別PDF生成
        pdf_filename = f"recommend_{rank}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        try:
            generate_single_pdf(item, rank=rank, output_pdf_path=pdf_path)
            item["pdf_url"] = f"pdf/{pdf_filename}"
            logger.info(f"Generated single PDF for #{rank}: {pdf_filename}")
        except Exception as e:
            logger.warning(f"Failed to generate single PDF for #{rank}: {e}")
            item["pdf_url"] = None

    # おすすめ5件のまとめPDF生成
    combined_pdf_filename = "pt_digest_top5.pdf"
    combined_pdf_path = os.path.join(pdf_dir, combined_pdf_filename)
    try:
        generate_combined_pdf(recommended, output_pdf_path=combined_pdf_path)
        config["combined_pdf_url"] = f"pdf/{combined_pdf_filename}"
        logger.info(f"Generated combined PDF: {combined_pdf_filename}")
    except Exception as e:
        logger.warning(f"Failed to generate combined PDF: {e}")
        config["combined_pdf_url"] = None

    # 6. docs/data.json と docs/index.html の生成 (おすすめ + PDFリンク + 2セクション構造)
    logger.info("Generating docs/data.json and docs/index.html...")
    generate_docs(papers=papers, policy_news=policy_news, recommended=recommended, config=config, docs_dir="docs")
    
    # 7. メール配信 (環境変数 MAIL_TO, SMTP_USER, SMTP_PASSWORD 設定時)
    logger.info("Checking email notification settings...")
    send_digest_email(recommended=recommended, policy_news=policy_news, papers=papers)
    
    logger.info(f"Successfully generated digest with {len(recommended)} recommended items (with PDFs), {len(policy_news)} policy news items, and {len(papers)} research papers.")
    logger.info("=== Finished Successfully ===")

if __name__ == "__main__":
    main()
