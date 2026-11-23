"""Les trois modèles : naïf, meilleur, lourd. Plus la référence métier, qui n'est pas un modèle à nous.

  naïf      : la consommation de la même heure une semaine avant (168 h). Si le meilleur modèle
              ne le bat pas nettement, il y a un bug ou une fuite.
  meilleur  : une régression linéaire (OLS) sur le calendrier (heure × type de jour, mois) et les
              consommations passées, dans un Pipeline appris sur l'entraînement seulement.
  lourd     : à vous (jalon 2). La fonction heavy() dit quoi faire et refuse de tourner tant qu'elle
              n'est pas écrite. Ne la copiez pas d'un assistant sans pouvoir l'expliquer ligne par ligne.
  référence : la prévision J-1 publiée par RTE (colonne prevision_j1). C'est le seuil d'utilité du
              cahier des charges : un modèle qui ne la bat pas ne sert pas le décideur.

Attention : on sauve le Pipeline entier (prétraitement + modèle). Un modèle sauvé sans son
prétraitement ne sert à rien : personne ne sait plus quelles catégories il attend.
"""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression

from energie.config import ROOT, load_config
from energie.features import make_pipeline, split_xy
from energie.split import load_fold

MODELS_DIR = ROOT / "models"


class SameHourLastWeek(BaseEstimator, RegressorMixin):
    """Le modèle naïf : la consommation de la même heure, 168 h plus tôt. Il n'apprend rien."""

    column = "conso_moins_168h"

    def fit(self, X, y=None):
        if self.column not in X.columns:
            raise ValueError(f"le modèle naïf a besoin de la colonne {self.column} (lags_heures doit contenir 168)")
        self.is_fitted_ = True
        return self

    def predict(self, X):
        return np.asarray(X[self.column], dtype=float)


def naive(cfg: dict):
    X, y = split_xy(load_fold("train"), cfg)
    return SameHourLastWeek().fit(X, y)


def baseline(cfg: dict):
    """L'OLS : moindres carrés ordinaires sur les indicatrices du calendrier et les retards standardisés."""
    X, y = split_xy(load_fold("train"), cfg)
    return make_pipeline(LinearRegression(), cfg).fit(X, y)


def heavy(cfg: dict):
    """Le modèle lourd : jalon 2, à vous.

    Ce qu'on attend (cahier des charges, ligne 6) :
      1. un gradient boosting dans le même make_pipeline() : XGBRegressor (déjà dans requirements.lock),
         ou LightGBM après l'avoir ajouté à requirements.in puis régénéré le lock ; random_state=cfg["seed"] ;
      2. ses hyperparamètres choisis par validation croisée temporelle sur le pli d'entraînement
         SEULEMENT (TimeSeriesSplit, jamais KFold mélangé) ;
      3. la règle du champion écrite dans DECISIONS.md AVANT de lancer make compare ;
      4. un intervalle de confiance sur l'écart de MAE avec l'OLS (bootstrap par blocs de jours).
    Pièges : ne pas chercher les hyperparamètres sur la validation ; ne pas lire le test ;
    ne pas ajouter de variable publiée en même temps que la consommation.
    """
    raise NotImplementedError("Le modèle lourd est le travail du jalon 2 : lisez la docstring de heavy().")


def save_model(model, name: str) -> Path:
    MODELS_DIR.mkdir(exist_ok=True)
    path = MODELS_DIR / f"{name}.pkl"
    with open(path, "wb") as f:
        pickle.dump(model, f)
    return path


def load_model(name: str):
    path = MODELS_DIR / f"{name}.pkl"
    if not path.exists():
        raise FileNotFoundError(f"{path.name} manque : lancez make train")
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Entraîne le modèle naïf et l'OLS.")
    p.add_argument("--config", default="config.yaml")
    a = p.parse_args()
    cfg = load_config(a.config)
    # On passe par le module importé, pas par __main__ : sinon le pickle du modèle naïf
    # retiendrait « __main__.SameHourLastWeek » et ne se rechargerait plus depuis les autres scripts.
    import energie.model as mod

    for name, fn in (("naive", mod.naive), ("baseline", mod.baseline)):
        m = fn(cfg)
        path = mod.save_model(m, name)
        print(f"{name:9s} entraîné, sauvé dans {path.relative_to(ROOT)}")
