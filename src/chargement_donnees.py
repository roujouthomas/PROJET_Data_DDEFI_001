# %% [markdown]
# # Chargement des données éCO₂mix (version reproductible)
#
# Remplace l'ancien chargement (`files.upload()` + filtre sur « Données consolidées ») :
# - **téléchargement scripté** du jeu complet depuis l'API ODRE, sans clic manuel ;
# - **tout l'historique** : « Données définitives » (2012-2025) **et** « Données consolidées » (2026) ;
# - une empreinte SHA-256 du fichier brut, pour figer la version des données (exigé au jalon 2).
#
# Source : RTE, éCO₂mix national consolidé et définitif, sur ODRE.
# Licence : Licence Ouverte v2.0 (Etalab), réutilisation libre avec citation de la source.

# %%
import hashlib
from pathlib import Path

import pandas as pd
import requests

try:  # display() existe dans Colab/Jupyter ; en ligne de commande on se rabat sur print()
    display
except NameError:
    display = print

DATASET = "eco2mix-national-cons-def"
URL = (
    "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
    f"{DATASET}/exports/csv?delimiter=%3B"
)
RAW = Path("data/raw/eco2mix_national.csv")


def telecharger(url: str = URL, dest: Path = RAW) -> Path:
    """Télécharge le CSV complet une seule fois (environ 100 Mo), puis réutilise le fichier."""
    if dest.exists():
        print(f"Déjà téléchargé : {dest}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for bloc in r.iter_content(chunk_size=1 << 20):
                f.write(bloc)
    tmp.rename(dest)
    print(f"Téléchargé : {dest} ({dest.stat().st_size / 1e6:.0f} Mo)")
    return dest


def empreinte(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


chemin = telecharger()
print("SHA-256 :", empreinte(chemin))

# %%
# Lecture : on garde les deux natures de données. Les définitives (2012-2025) font 95 % de l'historique.
df = pd.read_csv(chemin, sep=";", encoding="utf-8-sig", low_memory=False)

# Horodatage en UTC, puis heure de Paris : la consommation suit l'heure légale (changements d'heure inclus).
df["date_heure"] = pd.to_datetime(df["date_heure"], utc=True).dt.tz_convert("Europe/Paris")
df = df.sort_values("date_heure").drop_duplicates("date_heure").reset_index(drop=True)

print("Lignes :", len(df))
print("Période :", df["date_heure"].min(), "->", df["date_heure"].max())
print(df["nature"].value_counts())

# %%
# Agrégation horaire sur tout l'historique.
# Au pas de 15 min, la consommation n'est mesurée qu'un quart d'heure sur deux (les autres sont vides) :
# la moyenne horaire ignore ces trous.
COLONNES = [
    "consommation",   # la cible : consommation réalisée (MW)
    "prevision_j1",   # prévision RTE publiée la veille : la référence à battre
    "prevision_j",    # prévision RTE du jour même : ne pas utiliser comme variable (connue trop tard)
    "nucleaire", "hydraulique", "eolien", "solaire", "gaz", "charbon", "fioul", "bioenergies",
]
horaire = (
    df.set_index("date_heure")[COLONNES]
    .apply(pd.to_numeric, errors="coerce")
    .resample("h")
    .mean()
)

print("Heures :", len(horaire))
print("Heures sans consommation :", int(horaire["consommation"].isna().sum()))
display(horaire.groupby(horaire.index.year)["consommation"].agg(["count", "mean"]).round(0))

# %%
# Premier repère pour le cadrage : l'erreur de la prévision J-1 de RTE.
# C'est le niveau que notre modèle devra battre (le « seuil d'utilité » du cahier des charges).
ok = horaire.dropna(subset=["consommation", "prevision_j1"])
erreur = (ok["prevision_j1"] - ok["consommation"]).abs()
print(f"Erreur absolue moyenne de la prévision J-1 de RTE : {erreur.mean():.0f} MW")
print(f"En % de la consommation moyenne : {100 * erreur.mean() / ok['consommation'].mean():.1f} %")
display(erreur.groupby(erreur.index.year).mean().round(0).to_frame("MAE J-1 RTE (MW)"))

# %% [markdown]
# ⚠️ **Attention aux fuites de données pour la suite.** La production par filière (nucléaire, éolien, etc.),
# les échanges et `prevision_j` sont mesurés ou publiés **en même temps** que la consommation à prédire.
# Pour une prévision faite la veille, ils ne peuvent servir que **décalés d'au moins 24 h**.
