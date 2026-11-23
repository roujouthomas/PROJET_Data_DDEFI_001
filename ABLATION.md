# Étude d'ablation (jalon 1)

Pré-enregistrement d'abord, calcul ensuite. Vous écrivez vos prédictions dans une issue du dépôt (horodatée), puis seulement vous lancez le calcul et vous remplissez ce tableau.

Lien de l'issue de pré-enregistrement : [à coller]

Référence : l'OLS complet, MAE de validation 2024 = 2 388 MW (`metrics.json`).

| Groupe retiré | MAE prédite (MW) | MAE mesurée (validation) | Écart | Commentaire |
|---|---|---|---|---|
| Heure × type de jour (`heure_type_jour`) | | | | |
| Mois (`mois`) | | | | |
| Consommation à J-2 (`conso_moins_48h`) | | | | |
| Consommation à J-7 (`conso_moins_168h`) | | | | |
| Température (quand elle sera ajoutée) | | | | |

Règle : une ablation se fait en réentraînant le Pipeline sans le groupe, sur le même pli d'entraînement, et en mesurant sur la même validation. Pas en mettant les colonnes à zéro.
