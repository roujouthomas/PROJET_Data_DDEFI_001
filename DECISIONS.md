# Journal des décisions

Une entrée par décision, datée, avec l'alternative rejetée et la raison. L'équipe qui vous audite lit ce fichier avant le code.
Une décision sans alternative n'est pas une décision, c'est un constat.

## 2026-11-23 · Données : les définitives 2012-2025 seulement, empreinte sur le fichier horaire

- Décision : on télécharge par script l'export ODRE filtré sur les données définitives du 1er janvier 2012 au 31 décembre 2025, on l'agrège par heure, et on fige l'empreinte SHA-256 du fichier horaire.
- Alternative rejetée : garder aussi les données consolidées de 2026. Rejetée : RTE les révise encore, l'empreinte changerait chaque mois et `make reproduce` ne donnerait plus les mêmes chiffres.
- Preuve : `src/energie/data.py` ; `data/sha256.txt` ; `tests/test_data.py`. Un téléchargement neuf redonne la même empreinte et le même `metrics.json`.

## 2026-11-23 · Coupe chronologique : 2012-2023, 2024, 2025

- Décision : entraînement 2012-2023, validation 2024, test 2025, par années civiles en heure de Paris. Le test ne se lit qu'une fois, au jalon 2.
- Alternative rejetée : la coupe aléatoire du gabarit. Rejetée : sur une série temporelle, elle met dans l'entraînement l'heure qui suit une heure de validation, donc le modèle verrait le futur.
- Preuve : `config.yaml`, `split` ; `tests/test_split.py` fige les empreintes des plis et vérifie l'ordre chronologique.
- 2020 (confinements) : voir l'entrée du 2026-11-25.

## 2026-11-23 · Horizon de 36 heures, retards de 48 et 168 heures

- Décision : la prévision se fait la veille à midi pour les 24 heures du lendemain, donc jusqu'à 36 heures d'avance. Une consommation passée n'entre que si elle a au moins 36 heures. On prend la même heure 48 h (J-2) et 168 h (J-7) avant.
- Alternative rejetée : le retard de 24 h (la veille, même heure). Rejetée : pour prévoir 23 h le jour J, la consommation de 23 h la veille n'est pas encore connue à midi. Ce serait une fuite.
- Preuve : `config.py` refuse un retard plus court que l'horizon ; `tests/test_leakage.py` modifie les données des 36 dernières heures et vérifie que les variables ne bougent pas.

## 2026-11-23 · Colonnes interdites : production, échanges, prévision J ; la prévision J-1 de RTE est la référence

- Décision : la production par filière, les échanges et la prévision J ne sont jamais des variables. La prévision J-1 de RTE n'est pas une variable non plus : c'est le seuil d'utilité à battre.
- Alternative rejetée : utiliser la prévision J-1 de RTE comme variable. Rejetée : notre modèle recopierait RTE au lieu de l'améliorer, et on ne pourrait plus mesurer ce qu'il apporte.
- Preuve : `config.yaml`, `excluded_features` ; `split_xy` refuse les colonnes interdites.

## 2026-11-23 · Naïf J-7, meilleur OLS

- Décision : le modèle naïf prévoit la consommation de la même heure une semaine avant. Le meilleur modèle est une régression linéaire (OLS) sur l'heure croisée avec le type de jour (semaine, samedi, dimanche ou férié), le mois et les retards de 48 h et 168 h.
- Alternative rejetée : la moyenne de l'entraînement comme modèle naïf. Rejetée : elle ignore le cycle de la journée et de la semaine, la barre serait trop basse.
- Résultat sur la validation 2024 : naïf 3 247 MW de MAE, OLS 2 388 MW, prévision J-1 de RTE 1 428 MW (`metrics.json`).
- À discuter : le lundi de Pentecôte est compté férié, alors qu'il est souvent travaillé depuis 2005 (journée de solidarité).

## 2026-11-23 · Coût asymétrique : pas de chiffre tant qu'il n'est pas sourcé

- Décision : `ratio_cout_sous_sur` vaut `null` dans `config.yaml`. Le coût asymétrique n'est pas calculé tant qu'on n'a pas estimé le rapport à partir des prix de règlement des écarts publiés par RTE.
- Alternative rejetée : mettre un rapport « raisonnable » au hasard. Rejetée : un chiffre inventé n'est pas une hypothèse, c'est une erreur.

## 2026-11-25 · Heure de décision : la veille à midi

- Décision : la prévision est publiée la veille à midi pour les 24 heures du lendemain. C'est un choix de conception de notre persona, qui fixe l'horizon (12 à 36 h) et la règle anti-fuite.
- Alternative rejetée : décider le soir (18 h). Rejetée : moins de temps pour programmer les moyens du lendemain, et un gain de six heures de données seulement.

## 2026-11-25 · 2020 reste dans l'entraînement, son effet sera mesuré

- Décision : on garde 2020 dans le pli d'entraînement. Au jalon 2, on réentraîne l'OLS sans 2020 et on compare la MAE de validation.
- Alternative rejetée : retirer 2020 d'office. Rejetée : on perdrait une année entière sur une impression, sans mesurer si elle dégrade vraiment le modèle.

## 2026-11-25 · Le biais de RTE est un décalage systématique : on compare aussi à RTE corrigée

- Constat : depuis 2023, la prévision J-1 de RTE est environ 1 100 MW sous la consommation publiée. La prévision du jour même a le même écart, à chaque trimestre, y compris dans les données consolidées de 2026 : c'est un décalage de définition, pas une erreur de prévision.
- Décision : `metrics.json` donne aussi la prévision RTE corrigée de son écart moyen de l'année précédente (1 039 MW de MAE en 2024, contre 1 428 MW brute). C'est la barre qu'on se fixe.
- Alternative rejetée : ne comparer qu'à la prévision brute. Rejetée : notre modèle la battrait en partie grâce à ce décalage, pas grâce à une meilleure prévision.
- Preuve : `src/energie/evaluate.py`, `rte_bias_previous_year` ; cahier des charges, section 3.

## 2026-11-25 · Plan : OLS au jalon 2, XGBoost au rendu final

- Décision : naïf J-7 ; meilleur = OLS (jalon 2, 29 janvier) ; lourd = XGBoost (rendu final), comparé à l'OLS avec des intervalles de confiance. Demandé par le professeur dans sa relecture du 24/11.
- Alternative rejetée : régression régularisée en naïf, XGBoost en meilleur et réseau de neurones (Transformer, CNN, TabPFN) en lourd, proposée dans le cahier le 23/11. Rejetée : le jalon 2 attend une OLS, et un réseau de neurones ne se justifie qu'après avoir montré ce que XGBoost n'arrive pas à faire. Il reste une piste si le temps le permet.

## 2026-11-25 · Température : Open-Meteo, observée pour apprendre, prévue pour évaluer

- Décision : température horaire Open-Meteo (CC BY 4.0). Observée (réanalyse ERA5) pour l'entraînement 2012-2023 ; prévue la veille (prévisions archivées) pour évaluer 2024 et 2025, en plus de l'observée.
- Alternatives rejetées : la température quotidienne régionale d'ODRE (seulement depuis 2016, au pas journalier) ; les stations Météo-France en source principale (un fichier par département, des stations qui ouvrent et ferment), gardées comme contrôle.
- À faire au jalon 2 : choisir les villes et leurs poids, vérifier heure par heure la couverture des prévisions archivées (des trous existent début 2024).

## À écrire avant `make compare` (jalon 2)

- **Règle du champion** : [quel modèle gagne, sur quelle métrique, avec quel intervalle, et ce qu'on fait en cas d'égalité]. Tant que ce titre n'est pas écrit ici, `make compare` refuse de tourner.
