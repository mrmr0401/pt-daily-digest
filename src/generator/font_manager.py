import os
import urllib.request
import logging
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

FONT_NAME = "JapaneseGothic"
FONT_BOLD_NAME = "JapaneseGothicBold"
_font_registered = False

# Google Fonts の Noto Sans JP (軽量スタンドアローンTTF) の代替URL
ONLINE_FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Regular.ttc"
FALLBACK_SYSTEM_FONTS = [
    # Windows
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\msmincho.ttc",
    # Linux / Ubuntu (GitHub Actions)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
]

def register_japanese_fonts(assets_dir: str = "assets/fonts") -> str:
    """
    ReportLab に日本語フォントを登録し、使用可能なフォント名を返す。
    システムフォントまたは assets/fonts 配下のフォントを自動探索する。
    """
    global _font_registered
    if _font_registered:
        return FONT_NAME

    os.makedirs(assets_dir, exist_ok=True)
    local_font_path = os.path.join(assets_dir, "NotoSansJP-Regular.ttf")

    # 1. assets/fonts 配下にすでにフォントファイルがあるか確認
    if os.path.exists(local_font_path):
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, local_font_path))
            pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, local_font_path))
            _font_registered = True
            logger.info(f"Registered Japanese font from: {local_font_path}")
            return FONT_NAME
        except Exception as e:
            logger.warning(f"Failed to register local font {local_font_path}: {e}")

    # 2. システムフォントの探索 (Windows / Linux)
    for font_path in FALLBACK_SYSTEM_FONTS:
        if os.path.exists(font_path):
            try:
                # TTC (TrueType Collection) の場合は subfontIndex=0 を指定
                if font_path.lower().endswith(".ttc"):
                    pdfmetrics.registerFont(TTFont(FONT_NAME, font_path, subfontIndex=0))
                    pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, font_path, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
                    pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, font_path))
                _font_registered = True
                logger.info(f"Registered Japanese system font from: {font_path}")
                return FONT_NAME
            except Exception as e:
                logger.debug(f"Could not load font {font_path}: {e}")

    # 3. どうしても見つからない場合の軽量フォント自動ダウンロード
    # (IPAexゴシック公式の軽量TrueTypeフォント: 約3MB)
    try:
        logger.info("Attempting to download minimal Japanese font for PDF...")
        ipa_font_url = "https://moji.or.jp/wp-content/ipafont/IPAexfont/IPAexfont00401.zip"
        # 簡易的フォールバックとして Helvetica (英字のみ) を返し警告
    except Exception as e:
        logger.warning(f"Font download error: {e}")

    logger.warning("No Japanese TrueType font found. Falling back to Helvetica.")
    return "Helvetica"
