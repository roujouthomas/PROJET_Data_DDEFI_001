"""Les données : téléchargement, agrégation horaire, empreinte, contrat de schéma.

Source : RTE, « Données éCO₂mix nationales consolidées et définitives », plateforme ODRE,
jeu eco2mix-national-cons-def, Licence Ouverte v2.0 (Etalab).
On ne garde que les données définitives de la période de config.yaml (2012-2025) : les données
consolidées de l'année en cours sont encore révisées, elles feraient changer l'empreinte.

Deux fichiers, jamais versionnés (data/raw/ est dans .gitignore) :
  - eco2mix_definitif_15min.csv : l'export ODRE tel quel, au pas de 15 minutes ;
  - eco2mix_horaire.csv : la moyenne horaire, horodatée en UTC, écrite dans un format fixe.
On versionne l'empreinte SHA-256 du fichier horaire (data/sha256.txt) : si les données changent,
make reproduce s'arrête et le dit. On hache le fichier horaire plutôt que l'export brut, parce
que l'export peut changer de forme (ordre des colonnes, guillemets) sans que les chiffres changent.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd
import requests

from energie.config import ROOT, load_config

EXPORT = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-cons-def/exports/csv"
RAW_DIR = ROOT / "data" / "raw"
RAW_15MIN = RAW_DIR / "eco2mix_definitif_15min.csv"
RAW_HORAIRE = RAW_DIR / "eco2mix_horaire.csv"
TARGET = "consommation"
REFERENCE = "prevision_j1"  # la prévision publiée la veille par RTE : la référence à battre

# Le contrat de schéma du fichier horaire. Un test l'applique (tests/test_data.py).
SCHEMA = {
    "columns": ["date_heure", TARGET, REFERENCE],
    # Bornes physiques larges de la consommation française : le minimum historique est
    # au-dessus de 25 GW, le record (février 2012) un peu au-dessus de 100 GW.
    "conso_min_mw": 20_000,
    "conso_max_mw": 110_000,
    # Heures sans consommation tolérées sur 14 ans (environ 123 000 heures).
    "max_heures_manquantes": 50,
}


def sha256(path: Path) -> str:
    """L'empreinte d'un fichier, lue par blocs pour ne pas charger un gros fichier en mémoire."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def heures_attendues(cfg: dict) -> pd.DatetimeIndex:
    """Toutes les heures de la période, en heure de Paris, converties en UTC (changements d'heure compris)."""
    debut = pd.Timestamp(cfg["periode"]["debut"], tz="Europe/Paris")
    fin = pd.Timestamp(cfg["periode"]["fin"], tz="Europe/Paris") + pd.Timedelta(days=1)
    return pd.date_range(debut.tz_convert("UTC"), fin.tz_convert("UTC"), freq="h", inclusive="left")


def download(cfg: dict, force: bool = False) -> Path:
    """Télécharge l'export ODRE filtré (définitives, période, 4 colonnes). Environ 30 Mo, une seule fois."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_15MIN.exists() and not force:
        return RAW_15MIN
    heures = heures_attendues(cfg)
    params = {
        "delimiter": ";",
        "select": f"date_heure,nature,{TARGET},{REFERENCE}",
        "where": (
            "nature = 'Données définitives'"
            f" and date_heure >= date'{heures[0].isoformat()}'"
            f" and date_heure <= date'{(heures[-1] + pd.Timedelta(hours=1)).isoformat()}'"
        ),
        "order_by": "date_heure",
    }
    print(f"Téléchargement de {EXPORT} (environ 30 Mo, une à deux minutes)")
    tmp = RAW_15MIN.with_suffix(".part")
    with requests.get(EXPORT, params=params, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for bloc in r.iter_content(chunk_size=1 << 20):
                f.write(bloc)
    tmp.rename(RAW_15MIN)
    return RAW_15MIN


def build_hourly(cfg: dict, force: bool = False) -> Path:
    """Agrège le quart d'heure en heures et écrit le fichier horaire dans un format fixe.

    Au pas de 15 minutes, la consommation n'est renseignée qu'un quart d'heure sur deux :
    la moyenne horaire ignore les trous. Une heure sans aucune mesure reste vide (NaN).
    """
    if RAW_HORAIRE.exists() and not force:
        return RAW_HORAIRE
    df = pd.read_csv(download(cfg), sep=";", encoding="utf-8-sig")
    df["date_heure"] = pd.to_datetime(df["date_heure"], utc=True)
    df = df.sort_values("date_heure").drop_duplicates("date_heure")
    horaire = (
        df.set_index("date_heure")[[TARGET, REFERENCE]]
        .apply(pd.to_numeric, errors="coerce")
        .resample("h")
        .mean()
        .reindex(heures_attendues(cfg))
    )
    horaire.index.name = "date_heure"
    horaire = horaire.reset_index()
    horaire["date_heure"] = horaire["date_heure"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    horaire.to_csv(RAW_HORAIRE, index=False, float_format="%.2f", lineterminator="\n")
    return RAW_HORAIRE


def load_raw(cfg: dict | None = None) -> pd.DataFrame:
    """Charge le fichier horaire (le construit s'il manque) et vérifie le contrat de schéma."""
    cfg = cfg or load_config()
    df = pd.read_csv(build_hourly(cfg))
    df["date_heure"] = pd.to_datetime(df["date_heure"], utc=True)
    check_schema(df, cfg)
    return df


def check_schema(df: pd.DataFrame, cfg: dict) -> None:
    """Le contrat : colonnes, une ligne par heure de la période, bornes physiques, manquants."""
    if list(df.columns) != SCHEMA["columns"]:
        raise ValueError(f"colonnes {list(df.columns)} au lieu de {SCHEMA['columns']}")
    attendues = heures_attendues(cfg)
    if len(df) != len(attendues) or not (pd.DatetimeIndex(df["date_heure"]) == attendues).all():
        raise ValueError("les heures ne couvrent pas exactement la période de config.yaml")
    conso = df[TARGET].dropna()
    if conso.min() < SCHEMA["conso_min_mw"] or conso.max() > SCHEMA["conso_max_mw"]:
        raise ValueError(f"consommation hors bornes : {conso.min():.0f} à {conso.max():.0f} MW")
    manquantes = int(df[TARGET].isna().sum())
    if manquantes > SCHEMA["max_heures_manquantes"]:
        raise ValueError(f"{manquantes} heures sans consommation (maximum {SCHEMA['max_heures_manquantes']})")


def check_hash(expected_file: Path, cfg: dict) -> None:
    """Compare l'empreinte du fichier horaire à celle attendue ; écrit le fichier d'empreinte s'il n'existe pas."""
    path = build_hourly(cfg)
    actual = sha256(path)
    if not expected_file.exists():
        expected_file.write_text(actual + "\n", encoding="utf-8")
        print(f"Empreinte écrite dans {expected_file} : {actual[:12]}…")
        return
    expected = expected_file.read_text(encoding="utf-8").strip()
    if actual != expected:
        raise SystemExit(
            "Les données ont changé : l'empreinte ne correspond pas à data/sha256.txt.\n"
            f"  attendue : {expected}\n  obtenue  : {actual}\n"
            "Ne modifiez pas l'empreinte sans écrire pourquoi dans DECISIONS.md."
        )
    print(f"Données vérifiées : {path.relative_to(ROOT)}, empreinte {actual[:12]}… conforme.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Télécharge éCO₂mix, agrège par heure et vérifie l'empreinte.")
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--check", type=Path, default=ROOT / "data" / "sha256.txt", help="fichier d'empreinte attendue")
    p.add_argument("--force", action="store_true", help="retélécharge et reconstruit même si les fichiers existent")
    a = p.parse_args()
    cfg = load_config(a.config)
    if a.force:
        download(cfg, force=True)
        build_hourly(cfg, force=True)
    check_hash(a.check, cfg)
    df = load_raw(cfg)
    print(f"{len(df)} heures, {int(df[TARGET].isna().sum())} sans consommation, "
          f"du {df['date_heure'].iloc[0]} au {df['date_heure'].iloc[-1]} (UTC).")
