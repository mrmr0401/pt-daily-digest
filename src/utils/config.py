import os
import re
from typing import Dict, Any, List

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml")

def _simple_yaml_parse(content: str) -> Dict[str, Any]:
    """外部ライブラリ不使用の簡易YAMLパーサー (keyword_translations等のネストにも対応)"""
    config: Dict[str, Any] = {
        "keywords": [],
        "keyword_translations": {},
        "policy_keywords": [],
        "days_back": 14,
        "max_results_per_keyword": 20
    }
    
    current_top_key = None
    current_sub_key = None
    
    for line in content.splitlines():
        line_strip = line.strip()
        if not line_strip or line_strip.startswith("#"):
            continue
            
        indent = len(line) - len(line.lstrip())
        
        # トップレベルキー (インデントなし)
        if indent == 0 and ":" in line_strip:
            key, val = line_strip.split(":", 1)
            key = key.strip()
            val = val.strip()
            current_top_key = key
            current_sub_key = None
            if not val:
                if key == "keyword_translations":
                    config[key] = {}
                elif key not in config:
                    config[key] = []
            else:
                val_clean = val.strip('"').strip("'")
                if val_clean.isdigit():
                    config[key] = int(val_clean)
                else:
                    config[key] = val_clean
            continue
            
        # サブレベル (インデントあり)
        if current_top_key:
            # リスト要素 (- "item")
            if line_strip.startswith("-"):
                val = line_strip.lstrip("-").strip().strip('"').strip("'")
                if current_top_key == "keyword_translations" and current_sub_key:
                    config["keyword_translations"].setdefault(current_sub_key, []).append(val)
                elif isinstance(config.get(current_top_key), list):
                    config[current_top_key].append(val)
                continue
                
            # keyword_translations 内の サブキー: (例: 理学療法:)
            if current_top_key == "keyword_translations" and ":" in line_strip:
                sub_k, sub_v = line_strip.split(":", 1)
                sub_k = sub_k.strip().strip('"').strip("'")
                sub_v = sub_v.strip()
                current_sub_key = sub_k
                if sub_v:
                    # インライン配列 [ "a", "b" ] のパース
                    if sub_v.startswith("[") and sub_v.endswith("]"):
                        items = [x.strip().strip('"').strip("'") for x in sub_v[1:-1].split(",") if x.strip()]
                        config["keyword_translations"][sub_k] = items
                    else:
                        config["keyword_translations"][sub_k] = [sub_v.strip('"').strip("'")]
                else:
                    config["keyword_translations"][sub_k] = []
                continue
                
    return config

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """config.yaml から設定情報を読み込む (PyYAML優先・フォールバック対応)"""
    default_res = {
        "keywords": ["理学療法", "脳卒中 リハビリ", "フレイル"],
        "keyword_translations": {
            "理学療法": ["physical therapy", "physiotherapy"]
        },
        "policy_keywords": ["リハビリ", "疾患別リハビリテーション", "診療報酬", "疑義解釈", "理学療法", "介護報酬"],
        "days_back": 14,
        "max_results_per_keyword": 20
    }
    
    if not os.path.exists(config_path):
        return default_res
        
    try:
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            if cfg:
                return cfg
    except Exception:
        pass

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            return _simple_yaml_parse(content)
    except Exception:
        return default_res
