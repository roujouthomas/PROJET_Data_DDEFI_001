"""Test 3, pas de fuite : aucune variable ne dépend d'une information inconnue la veille à midi.

C'est le test le plus important du projet. La décision se prend la veille à midi pour les
24 heures du lendemain : pour l'heure t, rien de postérieur à t - 36 h ne doit entrer.
"""

from datetime import date

import numpy as np
import pandas as pd

from energie.data import TARGET
from energie.features import build_table, feature_columns, jours_feries, paques


def test_no_forbidden_column(cfg):
    assert not set(feature_columns(cfg)) & set(cfg["excluded_features"])
    assert all(h >= cfg["horizon_max_heures"] for h in cfg["lags_heures"])


def test_features_ignore_the_last_36_hours(raw, cfg):
    """On remplace par n'importe quoi la consommation après l'instant T : les variables des heures
    jusqu'à T + 36 h ne doivent pas bouger. Si l'une bouge, elle regardait trop près du présent."""
    t0 = pd.Timestamp("2024-03-15T11:00:00Z")
    abime = raw.copy()
    apres = abime["date_heure"] > t0
    abime.loc[apres, TARGET] = np.random.default_rng(0).uniform(0, 1e6, apres.sum())
    a, b = build_table(raw, cfg), build_table(abime, cfg)
    fenetre = a["date_heure"] <= t0 + pd.Timedelta(hours=cfg["horizon_max_heures"])
    cols = feature_columns(cfg)
    pd.testing.assert_frame_equal(a.loc[fenetre, cols], b.loc[fenetre, cols])


def test_calendar_is_known_in_advance():
    """Le calendrier se calcule sans données : Pâques et les fériés sont des règles fixes."""
    assert paques(2024) == date(2024, 3, 31)
    assert paques(2025) == date(2025, 4, 20)
    f = jours_feries(2025)
    assert len(f) == 11
    assert {date(2025, 4, 21), date(2025, 5, 29), date(2025, 6, 9), date(2025, 7, 14)} <= f
