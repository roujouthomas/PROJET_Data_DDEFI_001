"""Batch 4 : évaluer. Les métriques des modèles sauvés et de la référence RTE sur la validation, dans metrics.json.

    python batch/evaluate.py

Le pli de test est interdit ici : il ne se lit qu'avec make compare, une fois, au jalon 2.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from energie.config import ROOT, load_config  # noqa: E402
from energie.evaluate import evaluate_models, print_table  # noqa: E402

if __name__ == "__main__":
    cfg = load_config()
    res = evaluate_models(cfg, "validation")
    (ROOT / "metrics.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print_table(res)
