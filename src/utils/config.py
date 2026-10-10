import os
import re
from typing import Dict, Any, List

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml")

def _simple_yaml_parse(content: str) -> Dict[str, Any]:
    """外部ライブラリ不使用の簡易YAMLパーサー (config.yaml専用)"""
    config: Dict[str, Any] = {
        "keywords": [],
        "days_back": 7,
        "max_results_per_keyword": 20
    }
    
    current_key = None
    
    for line in content.splitlines():
        line_strip = line.strip()
        if not line_strip or line_strip.startswith("#"):
            continue
        
        # リスト要素 (- "item")
        if line_strip.startswith("-"):
            val = line_strip.lstrip("-").strip().strip('"').strip("'")
            if current_key and isinstance(config.get(current_key), list):
                config[current_key].append(val)
            continue
        
        # キー: バリュー
        if ":" in line_strip:
            key, val = line_strip.split(":", 1)
            key = key.strip()
            val = val.strip()
            
            current_key = key
            if not val:
                # 空の場合はリストの開始と仮定
                if key not in config or not isinstance(config[key], list):
                    config[key] = []
            else:
                # 数値や文字列の判別
                val_clean = val.strip('"').strip("'")
                if val_clean.isdigit():
                    config[key] = int(val_clean)
                else:
                    config[key] = val_clean
                    
    return config

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """config.yaml から設定情報を読み込む (PyYAML不要・標準ライブラリのみで動作)"""
    default_res = {
        "keywords": ["stroke rehabilitation", "frailty", "physical therapy"],
        "days_back": 7,
        "max_results_per_keyword": 20
    }
    
    if not os.path.exists(config_path):
        return default_res
        
    try:
        # PyYAMLが使える場合はPyYAMLを使用
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        # PyYAMLがない場合やエラー時は自前の簡易パーサーを使用
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
                return _simple_yaml_parse(content)
        except Exception:
            return default_res
