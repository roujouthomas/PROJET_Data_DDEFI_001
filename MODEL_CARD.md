# Fiche de modèle (model card)

D'après Mitchell et al. (2019), « Model Cards for Model Reporting ». Version 1 : le modèle de référence. Version 2 au jalon 2, avec le modèle lourd.

| | |
|---|---|
| Modèle | Régression linéaire (OLS) sur un Pipeline : indicatrices du calendrier, retards standardisés |
| Usage prévu | Proposer au responsable de la prévision de RTE, la veille à midi, une consommation horaire nationale pour le lendemain |
| Usage exclu | Décision automatique sans contrôle humain ; prévision régionale ; prévision infrajournalière ; événements exceptionnels |
| Données d'entraînement | 104 988 heures de 2012 à 2023 (pli `train`), coupe chronologique figée |
| Variables | `heure_type_jour` (heure × semaine, samedi, dimanche ou férié), `mois`, consommation à J-2 et à J-7 |
| Métriques sur la validation (2024, 8 781 heures) | MAE 2 388 MW (4,8 %), biais +860 MW ; référence RTE J-1 : 1 428 MW brute, 1 039 MW corrigée de son écart moyen de 2023 (`metrics.json`) |
| Limites connues | Pas de température : ne voit pas venir une vague de froid ou de chaleur. Ne bat pas encore la prévision J-1 de RTE. Surestime en moyenne en 2024 |
| Équité | Pas de personnes dans les données ; à la place, erreur par saison, par type de jour et par heure, au jalon 2 |
| Surveillance | À faire au jalon 3 : `MONITORING.md` |
