# PROJET_Data_DDEFI_001

Groupe 8

Thomas Roujou : Chef (ML specialist)
Thomas Traineau : Chef plus petit (IA specialist)
Martin goy : petite mains

fetch automatique pour recup la dernière version --> aller dans la case des commits --> fleches vers le bas --> mettre toujours 

---

# Prévision de la consommation électrique nationale (RTE éCO₂mix)

Prévoit, chaque veille à midi, la consommation électrique horaire de la France métropolitaine
pour les 24 heures du lendemain, afin d'aider le responsable de la prévision de RTE à faire
mieux que la prévision J-1 actuelle. Le cadrage complet est dans `docs/cahier-des-charges.md`.

Données : RTE, « Données éCO₂mix nationales consolidées et définitives » (plateforme ODRE),
Licence Ouverte v2.0. On n'utilise que les données définitives 2012-2025.
Elles ne sont pas dans le dépôt : un script les télécharge et vérifie leur empreinte.

## Lancer

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.lock
make reproduce        # télécharge (environ 30 Mo), coupe, entraîne, mesure : metrics.json
make test             # les tests, quelques secondes une fois les données téléchargées
```

`make reproduce` doit donner deux fois les mêmes chiffres, chez vous et chez l'équipe qui vous audite.
Si ce n'est pas le cas, l'un des quatre a bougé : données, code, graine, environnement.

## Où est quoi

| Dossier | Contenu |
|---|---|
| `docs/cahier-des-charges.md` | la décision servie, en six lignes puis en détail ; modifié par pull request |
| `docs/git-branches.md` | comment on travaille à plusieurs : branches, pull requests, revue, conflits, tags |
| `DECISIONS.md` | le journal : une entrée datée par décision, avec l'alternative rejetée |
| `data/README.md` | l'origine des données, la licence, l'empreinte SHA-256 |
| `src/energie/` | le code qui compte : `data`, `split`, `features`, `model`, `evaluate`, `compare` |
| `src/chargement_donnees.py` | la première exploration du jeu complet 2012-2026 (toutes les colonnes) |
| `batch/` | les scripts de traitement par lots : préparer, entraîner, prédire, évaluer |
| `notebooks/` | `01_exploration.ipynb`, `chargement_donnees.ipynb` |
| `tests/` | contrat de schéma, coupe figée, absence de fuite, propriétés des modèles, robustesse |
| `app/` | une interface minimale : on choisit un jour, on voit notre prévision, celle de RTE et le réalisé |
| `config.yaml` | la graine, la période, la coupe par années, l'horizon, les retards, les colonnes interdites |
| `metrics.json`, `compare.json` | ce que `make reproduce` et `make compare` produisent |

## Les modèles

| Niveau | Modèle | Où | Quand |
|---|---|---|---|
| naïf | la consommation de la même heure une semaine avant | `energie.model.naive` | fait |
| meilleur | régression linéaire (OLS) : heure × type de jour, mois, consommations à J-2 et J-7 | `energie.model.baseline` | fait, à enrichir (température) |
| lourd | XGBoost comparé honnêtement à l'OLS | `energie.model.heavy` | **à faire**, rendu final |
| référence | la prévision J-1 publiée par RTE, brute et corrigée de son écart moyen de l'année précédente | colonne `prevision_j1` | le seuil d'utilité à battre |

Sur la validation (2024, `metrics.json`) :

| Prévision | MAE | Biais moyen | Heures sous-estimées |
|---|---|---|---|
| Naïf (J-7) | 3 247 MW (6,5 %) | −163 MW | 49 % |
| OLS, sans température | 2 388 MW (4,8 %) | +860 MW | 38 % |
| Prévision J-1 de RTE, brute | 1 428 MW (2,9 %) | −1 146 MW | 82 % |
| **Prévision J-1 de RTE, corrigée** | **1 039 MW (2,1 %)** | −15 MW | 50 % |

L'OLS bat nettement le naïf (le test `test_gain_over_naive_is_not_luck` le vérifie par bootstrap sur les jours),
mais pas encore RTE. Il lui manque la température, premier moteur de la consommation (cahier des charges, section 5).
La prévision brute de RTE est environ 1 100 MW sous le réalisé depuis 2023, de façon systématique (cahier des charges, section 3) :
la vraie barre est la prévision corrigée de cet écart, mesuré sur l'année précédente.

## Règles du dépôt

- Les notebooks importent `src/energie`, ils ne le recopient pas.
- Tout ce qui est appris (catégories, moyennes, coefficients) l'est sur le pli d'entraînement, jamais sur le jeu entier.
- La coupe est chronologique : entraînement 2012-2023, validation 2024, test 2025. Jamais de coupe aléatoire sur une série temporelle.
- Aucune variable postérieure à la veille midi : pas de production par filière, pas d'échanges, pas de prévision J, et `prevision_j1` n'est jamais une variable. `tests/test_leakage.py` le vérifie.
- Le jeu de test ne se lit qu'une fois, à `make compare`, quand la règle du champion est écrite dans `DECISIONS.md`.
- L'IA peut écrire du code ici ; à l'oral, vous devez pouvoir expliquer chaque ligne.

## Licence

Code : MIT. Données : RTE, éCO₂mix, Licence Ouverte v2.0 (Etalab), via la plateforme ODRE.
