"""Les métriques : deux lecteurs, deux familles.

Pour l'ingénieur : MAE en MW et en %, RMSE, biais (erreur moyenne signée), part des heures sous-estimées.
Pour le décideur : l'écart à la prévision J-1 de RTE (le seuil d'utilité), et le coût asymétrique
des écarts dès que config.yaml donne le rapport entre sous-estimation et surestimation.

Attention : une métrique se calcule sur le pli de validation pendant tout le cours.
Le pli de test ne sert qu'une fois, à make compare (jalon 2), après que la règle du champion
a été écrite dans DECISIONS.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from energie.config import ROOT, load_config
from energie.data import REFERENCE, TARGET
from energie.features import split_xy
from energie.model import load_model
from energie.split import FOLDS, load_fold


def asymmetric_cost(y, pred, ratio: float) -> float:
    """Coût moyen par heure, en « MW surestimés équivalents » : un MW sous-estimé pèse ratio fois plus."""
    e = np.asarray(pred, dtype=float) - np.asarray(y, dtype=float)
    return float(np.mean(np.where(e < 0, -ratio * e, e)))


def metrics(y, pred, ratio: float | None = None) -> dict:
    """Le bloc de métriques complet pour une prévision sur un pli. Les heures sans prévision sont ignorées."""
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    ok = ~np.isnan(pred) & ~np.isnan(y)
    y, pred = y[ok], pred[ok]
    e = pred - y
    out = {
        "n_heures": int(len(y)),
        "mae_mw": round(float(np.mean(np.abs(e))), 1),
        "mae_pct": round(float(100 * np.mean(np.abs(e)) / np.mean(y)), 2),
        "rmse_mw": round(float(np.sqrt(np.mean(e**2))), 1),
        "biais_mw": round(float(np.mean(e)), 1),
        "part_sous_estimee": round(float(np.mean(e < 0)), 4),
    }
    out["cout_asymetrique"] = None if ratio is None else round(asymmetric_cost(y, pred, ratio), 1)
    return out


def rte_bias_previous_year(cfg: dict, fold: str) -> float:
    """L'écart moyen (prévision J-1 de RTE moins réalisé) sur l'année qui précède le pli.

    Depuis 2023, la prévision de RTE est environ 1 100 MW sous la consommation publiée, de façon
    systématique (cahier des charges, section 3). Pour une comparaison honnête, on la corrige de cet
    écart, mesuré sur l'année précédente seulement : aucune information du pli évalué n'est utilisée.
    """
    annee = cfg["split"][fold][0] - 1
    pli = next(f for f in FOLDS if cfg["split"][f][0] <= annee <= cfg["split"][f][1])
    d = load_fold(pli)
    d = d[d["annee"] == annee]
    return float((d[REFERENCE] - d[TARGET]).mean())


def references(df, y, cfg: dict, fold: str, ratio) -> dict:
    """La prévision J-1 de RTE, brute et corrigée de son écart moyen de l'année précédente."""
    biais = rte_bias_previous_year(cfg, fold)
    corrigee = metrics(y, df[REFERENCE] - biais, ratio)
    corrigee["correction_mw"] = round(-biais, 1)
    return {"reference_rte_j1": metrics(y, df[REFERENCE], ratio), "reference_rte_j1_corrigee": corrigee}


def evaluate_models(cfg: dict, fold: str = "validation") -> dict:
    """Tous les modèles sauvés et les références RTE, sur un pli : le contenu de metrics.json."""
    df = load_fold(fold)
    X, y = split_xy(df, cfg)
    ratio = cfg.get("ratio_cout_sous_sur")
    a0, a1 = cfg["split"][fold]
    out = {"pli": fold, "annees": [a0, a1], "ratio_cout_sous_sur": ratio, "modeles": {}}
    for name in ("naive", "baseline"):
        out["modeles"][name] = metrics(y, load_model(name).predict(X), ratio)
    out["modeles"].update(references(df, y, cfg, fold, ratio))
    return out


def print_table(res: dict) -> None:
    for name, m in res["modeles"].items():
        print(f"{name:25s} MAE {m['mae_mw']:7.1f} MW ({m['mae_pct']:.2f} %)  RMSE {m['rmse_mw']:7.1f}  "
              f"biais {m['biais_mw']:+7.1f}  sous-estimée {100 * m['part_sous_estimee']:.0f} % des heures")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Les métriques des modèles sauvés, sur la validation.")
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--fold", default="validation", help="validation (toujours) ; test seulement via make compare")
    p.add_argument("--out", type=Path, default=ROOT / "metrics.json")
    a = p.parse_args()
    if a.fold == "test":
        raise SystemExit("Le pli de test ne se lit qu'avec make compare, une seule fois, au jalon 2.")
    cfg = load_config(a.config)
    res = evaluate_models(cfg, a.fold)
    a.out.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print_table(res)
