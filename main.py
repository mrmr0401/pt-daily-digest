import logging
from src.utils.config import load_config
from src.fetcher.aggregator import fetch_all_papers
from src.fetcher.mhlw_news import fetch_mhlw_news
from src.generator.html_builder import generate_docs

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
    
    # 4. docs/data.json と docs/index.html の生成 (2セクション構造)
    logger.info("Generating docs/data.json and docs/index.html...")
    generate_docs(papers=papers, policy_news=policy_news, config=config, docs_dir="docs")
    
    logger.info(f"Successfully generated digest with {len(policy_news)} policy news items and {len(papers)} research papers.")
    logger.info("=== Finished Successfully ===")

if __name__ == "__main__":
    main()
