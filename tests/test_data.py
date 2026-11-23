"""Test 1, le contrat de schéma : les données qui entrent sont celles qu'on attend.

Un test de ML n'est pas « la MAE est bonne ». C'est une propriété qui doit être vraie quoi qu'il
arrive : une ligne par heure, des bornes physiques, peu de manquants.
"""

import pandas as pd

from energie.data import SCHEMA, TARGET, heures_attendues


def test_schema_contract(raw, cfg):
    assert list(raw.columns) == SCHEMA["columns"]
    # Une ligne par heure de 2012 à 2025, changements d'heure compris : 14 ans, 122 736 heures.
    assert len(raw) == len(heures_attendues(cfg)) == 122_736
    assert raw["date_heure"].is_monotonic_increasing and raw["date_heure"].is_unique
    conso = raw[TARGET].dropna()
    assert SCHEMA["conso_min_mw"] < conso.min() and conso.max() < SCHEMA["conso_max_mw"]
    assert raw[TARGET].isna().sum() <= SCHEMA["max_heures_manquantes"]


def test_hourly_index_follows_paris_time(cfg):
    """La période commence le 1er janvier 2012 à minuit à Paris, soit 23 h UTC la veille."""
    h = heures_attendues(cfg)
    assert h[0] == pd.Timestamp("2011-12-31T23:00:00Z")
    assert h[-1] == pd.Timestamp("2025-12-31T22:00:00Z")
