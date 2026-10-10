import sys
import logging
from src.utils.config import load_config
from src.fetcher.aggregator import fetch_all_papers
from src.generator.html_builder import generate_docs

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== PT Daily Digest: Step 1 Processing Started ===")
    
    # 1. 設定ファイルの読み込み
    config = load_config()
    keywords = config.get("keywords", ["stroke rehabilitation", "frailty", "physical therapy"])
    days_back = config.get("days_back", 7)
    max_results = config.get("max_results_per_keyword", 20)
    
    logger.info(f"Keywords: {keywords}")
    logger.info(f"Days back: {days_back}, Max results per keyword: {max_results}")
    
    # 2. 論文データの取得 & 重複排除
    papers = fetch_all_papers(keywords=keywords, days_back=days_back, max_per_keyword=max_results)
    
    # 3. docs/data.json と docs/index.html の生成
    generate_docs(papers=papers, keywords=keywords, docs_dir="docs")
    
    logger.info(f"Successfully generated docs/data.json & docs/index.html with {len(papers)} unique papers.")
    logger.info("=== Finished Successfully ===")

if __name__ == "__main__":
    main()
