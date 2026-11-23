"""Lecture de config.yaml : la graine, la période, la coupe par années, l'horizon, les retards."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path = "config.yaml") -> dict:
    """Lit la configuration et vérifie les champs dont le reste du code dépend."""
    with open(ROOT / path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for key in ("seed", "periode", "split", "horizon_max_heures", "lags_heures", "excluded_features"):
        if key not in cfg:
            raise KeyError(f"config.yaml : la clé « {key} » manque")
    (a0, a1), (v0, v1), (t0, t1) = cfg["split"]["train"], cfg["split"]["validation"], cfg["split"]["test"]
    if not (a0 <= a1 < v0 <= v1 < t0 <= t1):
        raise ValueError("config.yaml : la coupe doit être chronologique (train < validation < test)")
    trop_courts = [h for h in cfg["lags_heures"] if h < cfg["horizon_max_heures"]]
    if trop_courts:
        raise ValueError(f"config.yaml : retards {trop_courts} h inconnus à l'heure de décision (fuite)")
    return cfg
