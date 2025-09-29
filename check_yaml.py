# check_yaml.py
from pathlib import Path
import sys
try:
    import yaml
except ImportError:
    print("請先安裝 pyyaml：pip install pyyaml"); sys.exit(1)

p = Path("artist_lang_map.yaml")
try:
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    total = sum(len(v) for v in data.values() if isinstance(v, list)) if isinstance(data, dict) else 0
    print(f"✅ YAML OK，總藝人數：約 {total}")
except Exception as e:
    print("❌ YAML 解析失敗：", e)
