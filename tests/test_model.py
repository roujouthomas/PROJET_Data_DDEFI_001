"""Tests 4 à 8 : le code d'entraînement n'est pas cassé, la prédiction est stable, le modèle sauvé
est le modèle entraîné, le naïf fait ce qu'il dit, l'OLS bat le naïf."""

import pickle

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from energie.evaluate import metrics
from energie.features import lag_columns, make_pipeline, split_xy
from energie.model import MODELS_DIR, SameHourLastWeek, load_model
from energie.split import load_fold


def _synthetic(cfg, n=2000, seed=0):
    """Des données artificielles où la cible est exactement linéaire dans les variables."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "heure_type_jour": [f"{h:02d}_semaine" for h in rng.integers(0, 24, n)],
        "mois": rng.integers(1, 13, n),
    })
    for c in lag_columns(cfg):
        df[c] = rng.uniform(30_000, 90_000, n)
    df["consommation"] = (
        10_000 + 0.5 * df["conso_moins_168h"] + 0.3 * df["conso_moins_48h"]
        + 100 * df["heure_type_jour"].str[:2].astype(int) + 50 * df["mois"]
    )
    return df


def _ols(cfg, df):
    X, y = split_xy(df, cfg)
    return make_pipeline(LinearRegression(), cfg).fit(X, y), X, y


def test_ols_recovers_exact_linear_signal(cfg):
    pipe, X, y = _ols(cfg, _synthetic(cfg))
    # À l'arrondi près : moins d'un MW d'écart pour des consommations de l'ordre de 70 000 MW.
    assert np.max(np.abs(pipe.predict(X) - y)) < 1.0


def test_predict_invariant_to_row_permutation(cfg):
    pipe, X, _ = _ols(cfg, _synthetic(cfg, seed=1))
    perm = np.random.default_rng(2).permutation(len(X))
    assert np.allclose(pipe.predict(X)[perm], pipe.predict(X.iloc[perm]))


def test_loaded_pipeline_matches_trained(cfg, tmp_path):
    pipe, X, _ = _ols(cfg, _synthetic(cfg, seed=3))
    path = tmp_path / "m.pkl"
    path.write_bytes(pickle.dumps(pipe))
    again = pickle.loads(path.read_bytes())
    assert np.max(np.abs(pipe.predict(X) - again.predict(X))) < 1e-9


def test_naive_returns_same_hour_last_week(cfg):
    X, _ = split_xy(_synthetic(cfg, n=10), cfg)
    assert np.array_equal(SameHourLastWeek().fit(X).predict(X), X["conso_moins_168h"].to_numpy())


def test_metrics_on_a_known_case():
    m = metrics([100, 100, 100, 100], [90, 110, 100, 120], ratio=3.0)
    assert m["mae_mw"] == 10.0 and m["biais_mw"] == 5.0 and m["part_sous_estimee"] == 0.25
    # sous-estimation de 10 pondérée 3 fois : (30 + 10 + 0 + 20) / 4 = 15
    assert m["cout_asymetrique"] == 15.0


def test_baseline_beats_naive_on_validation(cfg):
    """Si make train a tourné : l'OLS doit battre nettement le naïf, sinon bug ou fuite."""
    if not (MODELS_DIR / "baseline.pkl").exists():
        return  # pas encore entraîné : rien à vérifier
    df = load_fold("validation")
    X, y = split_xy(df, cfg)
    mae_naif = metrics(y, load_model("naive").predict(X))["mae_mw"]
    mae_ols = metrics(y, load_model("baseline").predict(X))["mae_mw"]
    assert mae_ols < 0.9 * mae_naif
