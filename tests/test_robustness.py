"""Tests de robustesse : un modèle n'est pas « bon » parce que sa MAE est bonne.

Il est robuste quand il se comporte comme on l'attend quand les données bougent un peu.
Chaque test est une propriété écrite AVANT de voir les résultats. Ils ne tournent que si
make train a produit models/baseline.pkl (en CI, make reproduce le fait).
"""

import numpy as np
import pytest

from energie.features import split_xy
from energie.model import MODELS_DIR, load_model
from energie.split import load_fold

pytestmark = pytest.mark.skipif(not (MODELS_DIR / "baseline.pkl").exists(), reason="lancez make train")


@pytest.fixture(scope="module")
def val(cfg):
    df = load_fold("validation")
    X, y = split_xy(df, cfg)
    return df, X, y.to_numpy(), load_model("baseline"), load_model("naive")


def test_gain_over_naive_is_not_luck(val):
    """Bootstrap par jours (les heures d'un même jour ne sont pas indépendantes) : l'intervalle à 95 %
    du gain de MAE de l'OLS sur le naïf reste strictement positif."""
    df, X, y, ols, naif = val
    gain = np.abs(naif.predict(X) - y) - np.abs(ols.predict(X) - y)
    jours = df["date_heure"].dt.tz_convert("Europe/Paris").dt.date.to_numpy()
    _, idx = np.unique(jours, return_inverse=True)
    par_jour = np.bincount(idx, weights=gain) / np.bincount(idx)
    rng = np.random.default_rng(0)
    boot = [par_jour[rng.integers(0, len(par_jour), len(par_jour))].mean() for _ in range(1000)]
    lo, _ = np.percentile(boot, [2.5, 97.5])
    assert lo > 0, f"borne basse du gain : {lo:.0f} MW"


def test_small_noise_on_lags_changes_little(val):
    """1 % de bruit sur les consommations passées : aucune prévision ne bouge de plus de 3 %."""
    _, X, _, ols, _ = val
    rng = np.random.default_rng(1)
    Xn = X.copy()
    for c in [c for c in X.columns if c.startswith("conso_moins_")]:
        Xn[c] = Xn[c] * (1 + rng.normal(0, 0.01, len(Xn)))
    p, pn = ols.predict(X), ols.predict(Xn)
    assert np.max(np.abs(pn - p) / p) < 0.03


def test_higher_past_consumption_means_higher_forecast(val):
    """Monotonie : si la consommation d'il y a une semaine était plus haute, la prévision ne baisse pas."""
    _, X, _, ols, _ = val
    X2 = X.copy()
    X2["conso_moins_168h"] = X2["conso_moins_168h"] + 1000
    assert (ols.predict(X2) >= ols.predict(X) - 1e-6).all()


def test_absurd_inputs_give_finite_forecasts(val):
    """Des valeurs absurdes (une heure inconnue, une consommation nulle) ne font pas planter."""
    _, X, _, ols, _ = val
    Xe = X.iloc[:5].copy()
    Xe["heure_type_jour"] = "99_inconnu"
    Xe["conso_moins_48h"] = 0.0
    assert np.isfinite(ols.predict(Xe)).all()
