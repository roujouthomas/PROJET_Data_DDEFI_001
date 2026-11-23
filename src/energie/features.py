"""Les variables : ce qui entre dans le modèle, et comment.

Deux familles, toutes connues la veille à midi :
  - le calendrier, en heure de Paris : l'heure croisée avec le type de jour (semaine, samedi,
    dimanche ou férié), le mois. La consommation suit l'heure légale, pas l'heure UTC ;
  - les consommations passées : la même heure 48 h et 168 h (une semaine) avant.

Attention à trois choses.
  1. La fuite. À la décision (la veille à midi), la consommation de J-1 après midi n'est pas
     encore connue. Pour prévoir 23 h le jour J, la dernière heure connue date de 36 h avant.
     Tout retard plus court que horizon_max_heures est refusé par config.py, et un test vérifie
     qu'aucune variable ne bouge quand on modifie les données des 36 dernières heures.
  2. Les colonnes interdites (config.yaml, excluded_features) : la production par filière, les
     échanges et la prévision J sont publiés en même temps que la consommation. prevision_j1 est
     la référence à battre, jamais une variable.
  3. La température manque encore (cahier des charges, ligne 5, À COMPLÉTER). C'est le premier
     moteur de la consommation : sans elle, le modèle ne peut pas voir venir une vague de froid.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from energie.data import REFERENCE, TARGET

CATEGORICAL = ["heure_type_jour", "mois"]


def lag_columns(cfg: dict) -> list[str]:
    return [f"conso_moins_{h}h" for h in cfg["lags_heures"]]


def feature_columns(cfg: dict) -> list[str]:
    """Toutes les colonnes utilisées, dans un ordre fixe, moins celles exclues par config.yaml."""
    cols = CATEGORICAL + lag_columns(cfg)
    return [c for c in cols if c not in cfg["excluded_features"]]


def paques(annee: int) -> date:
    """Dimanche de Pâques (algorithme grégorien anonyme, dit de Meeus)."""
    a, b, c = annee % 19, annee // 100, annee % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    ll = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ll) // 451
    mois = (h + ll - 7 * m + 114) // 31
    jour = (h + ll - 7 * m + 114) % 31 + 1
    return date(annee, mois, jour)


def jours_feries(annee: int) -> set[date]:
    """Les onze jours fériés nationaux de métropole. Le lundi de Pentecôte est compté férié,
    bien qu'il soit souvent travaillé depuis 2005 (journée de solidarité) : choix à discuter."""
    p = paques(annee)
    fixes = [(1, 1), (5, 1), (5, 8), (7, 14), (8, 15), (11, 1), (11, 11), (12, 25)]
    return {date(annee, m, j) for m, j in fixes} | {p + timedelta(days=1), p + timedelta(days=39), p + timedelta(days=50)}


def build_table(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Une ligne par heure : horodatage, cible, référence RTE, variables.

    Les retards se calculent par décalage sur la série horaire complète (une ligne par heure UTC,
    sans trou : load_raw le garantit), donc décaler de 48 lignes, c'est remonter de 48 heures.
    Ils ne regardent que le passé : on peut les calculer avant la coupe sans fuite.
    """
    df = raw[["date_heure", TARGET, REFERENCE]].copy().reset_index(drop=True)
    pas = df["date_heure"].diff().dropna().unique()
    if len(pas) != 1 or pas[0] != np.timedelta64(1, "h"):
        raise ValueError("la série horaire a des trous : impossible de calculer les retards")
    local = df["date_heure"].dt.tz_convert("Europe/Paris")
    feries = set().union(*(jours_feries(a) for a in range(local.dt.year.min(), local.dt.year.max() + 1)))
    jour = local.dt.date
    type_jour = np.where(jour.isin(feries) | (local.dt.dayofweek == 6), "dimanche_ferie",
                         np.where(local.dt.dayofweek == 5, "samedi", "semaine"))
    df["annee"] = local.dt.year
    df["heure_type_jour"] = local.dt.hour.astype(str).str.zfill(2) + "_" + type_jour
    df["mois"] = local.dt.month
    for h, col in zip(cfg["lags_heures"], lag_columns(cfg)):
        df[col] = df[TARGET].shift(h)
    return df


def split_xy(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.Series]:
    """Sépare les variables et la cible d'un pli."""
    cols = feature_columns(cfg)
    forbidden = [c for c in cfg["excluded_features"] if c in cols]
    if forbidden:
        raise ValueError(f"colonnes interdites dans les variables : {forbidden}")
    return df[cols], df[TARGET].astype(float)


def preprocessor(cfg: dict) -> ColumnTransformer:
    """Le prétraitement, à placer en tête d'un Pipeline : il n'apprend que sur ce qu'on lui donne en fit."""
    cols = feature_columns(cfg)
    return ColumnTransformer(
        [
            ("cal", OneHotEncoder(handle_unknown="ignore"), [c for c in CATEGORICAL if c in cols]),
            ("lag", StandardScaler(), [c for c in lag_columns(cfg) if c in cols]),
        ]
    )


def make_pipeline(estimator, cfg: dict) -> Pipeline:
    """Prétraitement puis modèle, dans un seul objet : ce qu'on entraîne, sauve et recharge."""
    return Pipeline([("prep", preprocessor(cfg)), ("model", estimator)])
