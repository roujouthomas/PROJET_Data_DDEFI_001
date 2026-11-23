"""Une interface minimale : on choisit un jour de la validation, le modèle montre sa prévision.

    make app      (ou : streamlit run app/app.py)

Attention : l'interface ne contient aucune logique métier. Elle charge le même Pipeline que le
batch et les mêmes variables que src/energie. Si vous modifiez un calcul ici, il diverge du
reste du projet sans que personne ne s'en aperçoive.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from energie.config import load_config  # noqa: E402
from energie.data import REFERENCE, TARGET  # noqa: E402
from energie.features import feature_columns  # noqa: E402
from energie.model import load_model  # noqa: E402
from energie.split import load_fold  # noqa: E402

cfg = load_config()
st.title("Consommation électrique nationale : la prévision de la veille")
st.caption("OLS sur le calendrier et les consommations passées, comparée à la prévision J-1 de RTE (validation 2024).")

try:
    model = load_model("baseline")
    df = load_fold("validation")
except FileNotFoundError:
    st.error("Aucun modèle entraîné : lancez make reproduce.")
    st.stop()

df["jour"] = df["date_heure"].dt.tz_convert("Europe/Paris").dt.date
jour = st.date_input("Jour à prévoir", value=df["jour"].iloc[len(df) // 2], min_value=df["jour"].min(), max_value=df["jour"].max())
d = df[df["jour"] == jour]
if d.empty:
    st.warning("Pas de données pour ce jour.")
    st.stop()
heures = d["date_heure"].dt.tz_convert("Europe/Paris").dt.strftime("%H:%M")
courbes = pd.DataFrame({
    "Réalisé": d[TARGET].to_numpy(),
    "Notre prévision (OLS)": model.predict(d[feature_columns(cfg)]),
    "Prévision J-1 de RTE": d[REFERENCE].to_numpy(),
}, index=heures)
st.line_chart(courbes)
erreurs = (courbes.drop(columns="Réalisé").sub(courbes["Réalisé"], axis=0)).abs().mean().round(0)
st.write("Erreur absolue moyenne ce jour-là (MW) :", erreurs.to_dict())
