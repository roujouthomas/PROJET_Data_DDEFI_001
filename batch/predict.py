"""Batch 3 : prédire. Prévoit la consommation des heures d'un fichier CSV et l'écrit.

    python batch/predict.py --in data/processed/validation.csv --out predictions.csv

C'est ce que ferait le responsable de la prévision chaque veille à midi : un fichier entre (les
heures du lendemain avec leurs variables), un fichier sort, avec la consommation prévue en MW.
Le CSV d'entrée doit avoir les colonnes de feature_columns() ; la cible peut manquer : on prédit,
on ne mesure pas. Si la prévision J-1 de RTE est présente, elle est recopiée pour comparaison.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from energie.config import load_config  # noqa: E402
from energie.data import REFERENCE  # noqa: E402
from energie.features import feature_columns  # noqa: E402
from energie.model import load_model  # noqa: E402

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True, help="CSV des heures à prévoir")
    p.add_argument("--out", default="predictions.csv")
    p.add_argument("--model", default="baseline", choices=["naive", "baseline", "heavy"])
    a = p.parse_args()
    cfg = load_config()
    df = pd.read_csv(a.inp)
    cols = feature_columns(cfg)
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(f"colonnes manquantes dans {a.inp} : {missing}")
    out = pd.DataFrame({"date_heure": df["date_heure"], "prevision_mw": load_model(a.model).predict(df[cols]).round(0)})
    if REFERENCE in df.columns:
        out["prevision_rte_j1_mw"] = df[REFERENCE]
    out.to_csv(a.out, index=False)
    print(f"{len(out)} heures prévues avec « {a.model} » → {a.out}")
