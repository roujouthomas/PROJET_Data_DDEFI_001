"""make compare : les trois modèles et la référence RTE sur le pli de test, une seule fois, au jalon 2.

Règle du cours : on n'ouvre ce fichier qu'après avoir écrit dans DECISIONS.md la règle du
champion (quel modèle gagne, à quelle condition, avec quel intervalle). Le script le vérifie
grossièrement : il refuse de tourner si DECISIONS.md ne contient pas la ligne « Règle du champion ».
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energie.config import ROOT, load_config
from energie.data import REFERENCE
from energie.evaluate import metrics, print_table
from energie.features import split_xy
from energie.model import heavy, load_model, save_model
from energie.split import load_fold


def main(cfg: dict, out: Path) -> dict:
    decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    if "Règle du champion" not in decisions:
        raise SystemExit("Écrivez d'abord la « Règle du champion » dans DECISIONS.md, puis relancez make compare.")
    df = load_fold("test")
    X, y = split_xy(df, cfg)
    ratio = cfg.get("ratio_cout_sous_sur")
    out_d = {"pli": "test", "annees": cfg["split"]["test"], "modeles": {}}
    for name in ("naive", "baseline"):
        out_d["modeles"][name] = metrics(y, load_model(name).predict(X), ratio)
    try:
        hv = load_model("heavy")
    except FileNotFoundError:
        hv = heavy(cfg)  # lève NotImplementedError tant que le jalon 2 n'est pas fait
        save_model(hv, "heavy")
    out_d["modeles"]["heavy"] = metrics(y, hv.predict(X), ratio)
    out_d["modeles"]["reference_rte_j1"] = metrics(y, df[REFERENCE], ratio)
    out.write_text(json.dumps(out_d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_d


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--out", type=Path, default=ROOT / "compare.json")
    a = p.parse_args()
    print_table(main(load_config(a.config), a.out))
