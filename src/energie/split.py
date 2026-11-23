"""La coupe figée : entraînement, validation, test, par années civiles (config.yaml).

Attention : pour une série temporelle, la coupe n'est jamais aléatoire. Une coupe aléatoire
mettrait dans l'entraînement l'heure qui suit une heure de validation : le modèle verrait le futur.
Ici l'entraînement couvre 2012-2023, la validation 2024, le test 2025. Le pli de test ne se lit
qu'au jalon 2, une seule fois, avec make compare.

Les heures sans cible ou sans retard (début de série, heures manquantes) sont retirées des plis :
on ne peut ni apprendre ni mesurer sur elles. Leur nombre est affiché.

Chaque pli est haché : le test test_split_is_frozen vérifie que la coupe n'a pas bougé.
"""

from __future__ import annotations

import argparse
import hashlib

import pandas as pd

from energie.config import ROOT, load_config
from energie.data import TARGET, load_raw
from energie.features import build_table, lag_columns

PROCESSED = ROOT / "data" / "processed"
FOLDS = ("train", "validation", "test")


def make_split(raw: pd.DataFrame, cfg: dict) -> dict[str, pd.DataFrame]:
    """Construit la table des variables puis la coupe par années de l'heure de Paris."""
    table = build_table(raw, cfg)
    utilisables = table.dropna(subset=[TARGET] + lag_columns(cfg))
    folds = {}
    for name in FOLDS:
        a0, a1 = cfg["split"][name]
        folds[name] = utilisables[utilisables["annee"].between(a0, a1)].reset_index(drop=True)
    return folds


def fold_hash(df: pd.DataFrame) -> str:
    """L'empreinte d'un pli : la liste de ses heures, dans l'ordre."""
    heures = ",".join(pd.to_datetime(df["date_heure"], utc=True).dt.strftime("%Y-%m-%dT%H").tolist())
    return hashlib.sha256(heures.encode()).hexdigest()


def write_split(cfg: dict) -> dict[str, str]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    folds = make_split(load_raw(cfg), cfg)
    hashes = {}
    for name in FOLDS:
        folds[name].to_csv(PROCESSED / f"{name}.csv", index=False)
        hashes[name] = fold_hash(folds[name])
    (PROCESSED / "hashes.txt").write_text("".join(f"{k} {v}\n" for k, v in hashes.items()), encoding="utf-8")
    return hashes


def load_fold(name: str) -> pd.DataFrame:
    if name not in FOLDS:
        raise ValueError(f"pli inconnu : {name}")
    path = PROCESSED / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError("la coupe n'existe pas : lancez make split")
    df = pd.read_csv(path)
    df["date_heure"] = pd.to_datetime(df["date_heure"], utc=True)
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="La coupe figée train / validation / test.")
    p.add_argument("--config", default="config.yaml")
    a = p.parse_args()
    cfg = load_config(a.config)
    h = write_split(cfg)
    for name in FOLDS:
        df = load_fold(name)
        a0, a1 = cfg["split"][name]
        print(f"{name:11s} {a0}-{a1}  {len(df):6d} heures, consommation moyenne {df[TARGET].mean():,.0f} MW, "
              f"empreinte {h[name][:12]}…".replace(",", " "))
