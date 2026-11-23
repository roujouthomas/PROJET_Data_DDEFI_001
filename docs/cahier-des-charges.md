# Cahier des charges : Watt Data Conseil × RTE, prévision de la consommation électrique

> Jalon 1, projet data DDEFI 2026-2027, Centrale Méditerranée.
> Équipe : Thomas Roujou, Thomas Traineau, Martin Goy.
> Statut : **premier jet à relire en équipe**. Les passages marqués « À COMPLÉTER » ou « À VALIDER » sont à trancher avant le rendu.

## La persona : qui nous incarnons

Nous sommes **Watt Data Conseil**, un cabinet de conseil en données (fictif). Nous sommes mandatés par **la direction en charge de l'équilibre offre-demande de RTE**, le gestionnaire du réseau de transport d'électricité français. RTE doit garantir à chaque instant que la production égale la consommation. Pour cela, il s'appuie la veille sur une prévision de la consommation du lendemain, qui sert à dimensionner les marges et les réserves.

Notre interlocuteur est **le responsable de la prévision de consommation**. C'est lui qui valide la méthode et signe la mise en service d'un nouveau modèle. Le **dispatcher** du centre de conduite garde la décision opérationnelle finale.

## La question en une phrase

> Chaque veille, quelle consommation horaire nationale le responsable de la prévision de RTE doit-il retenir pour le lendemain, afin de **réduire l'erreur de prévision par rapport à la prévision J-1 actuelle**, dégradée depuis 2022, et donc **le volume de réserves activées en urgence** ?

| Marqueur | Dans notre question |
|---|---|
| Une décision | la consommation horaire retenue la veille pour le lendemain ou la semaine précédente pour celle d'après, qui fixe le niveau de marges et de réserves programmées |
| Une mesure | l'erreur absolue moyenne en MW par rapport au réalisé, et le coût des écarts qui en découle |
| Un périmètre | la France métropolitaine, les 24 heures du lendemain, chaque jour |
| Un responsable | le responsable de la prévision de consommation de RTE, qui signe ; le dispatcher, qui décide en temps réel |

## En six lignes

| Ligne | Réponse |
|---|---|
| **La décision servie** | Chaque veille, le responsable de la prévision de RTE retient la consommation attendue pour les 24 heures du lendemain, qui fixe les marges et réserves programmées. |
| **La cible** | `consommation` : consommation nationale réalisée, moyenne horaire en MW, horizon de 12 à 36 heures. |
| **La métrique** | Pour le décideur : un coût asymétrique des écarts (sous-estimer coûte plus cher). Pour l'ingénieur : MAE en MW et en %, erreur moyenne signée. Seuil d'utilité : battre la prévision J-1 de RTE. |
| **Les données** | RTE éCO₂mix national consolidé et définitif (ODRE), 2012-2026, Licence Ouverte v2.0, téléchargé par script avec empreinte SHA-256. Température et calendrier à ajouter. |
| **Les garde-fous** | Uniquement des informations connues la veille à midi ; production, échanges et prévision J interdits sauf décalés de 24 h ; météo prévue et non réalisée ; décision humaine ; aucune donnée personnelle ; position AI Act à argumenter. |
| **Les livrables** | Ce dépôt : `make reproduce`, tests et CI, `metrics.json`, comparaison Modèle linéaire / XG boost / Transformer/CNN, fiche de modèle, fiche de données, analyse AI Act, mémo client, interface. |

Le détail de chaque ligne suit.

## 1. La décision

**Qui et quand.** La veille du jour J, à midi (**hypothèse de travail À VALIDER** : l'heure exacte de publication de la prévision J-1 de RTE est à confirmer), le responsable de la prévision publie la consommation attendue pour chacune des 24 heures de J. Cette prévision fixe le volume de marges et de réserves que RTE programme pour J.

**Les options.** Retenir notre prévision, garder la prévision J-1 actuelle, ou combiner les deux.

**Ce que coûte chaque erreur.** Les deux erreurs n'ont pas le même prix :

- **Sous-estimer la consommation** (prévoir moins que le réalisé). RTE doit activer en urgence des moyens d'ajustement, souvent des centrales de pointe au gaz, au prix fort. Dans le pire cas, l'équilibre du réseau est menacé. C'est l'erreur la plus coûteuse.
- **Surestimer la consommation** (prévoir plus que le réalisé). RTE a réservé de la capacité qui ne sert pas. Le coût est réel, mais plus faible.

Le rapport exact entre ces deux coûts sera fixé à partir des prix de règlement des écarts publiés par RTE (**À COMPLÉTER**). D'ici là, notre hypothèse est qu'un MW sous-estimé coûte plus cher qu'un MW surestimé.

## 2. La cible

- **Colonne** : `consommation`, la consommation nationale réalisée, publiée par RTE au pas de 15 minutes puis agrégée par heure (moyenne en MW).
- **Horizon** : de 12 à 36 heures, puisqu'on prédit la veille à midi chacune des 24 heures du lendemain.
- **Date à laquelle on la connaît** : en temps réel pour une première valeur, puis en version consolidée et enfin définitive (environ un an plus tard).

**Ce que la cible ne capture pas** :
- la consommation **locale** : une prévision nationale juste peut cacher des erreurs régionales qui comptent pour le réseau ;
- le **coût réel en euros** de chaque écart, qui dépend du prix de l'électricité à cette heure-là ;
- la consommation qui ne passe pas par le réseau public, comme l'autoconsommation solaire.

## 3. La métrique

- **Métrique du modèle** : l'erreur absolue moyenne (MAE) en MW, lisible directement par le décideur (« on se trompe en moyenne de 1 000 MW »). En complément : la MAE en pourcentage de la consommation, et l'erreur moyenne signée, pour détecter un biais systématique.
- **Métrique métier** : un coût asymétrique des écarts, qui pénalise davantage la sous-estimation que la surestimation (le ratio vient de la ligne 1).
- **Seuil d'utilité** : le modèle n'a d'intérêt que s'il **fait mieux que la prévision J-1 actuelle de RTE**, mesurée sur des données jamais vues. Pour situer les ordres de grandeur, calculés sur nos données :

| Prévision | MAE 2024 | MAE 2025 |
|---|---|---|
| Naïve : la consommation de la même heure, une semaine avant | 3 247 MW | 3 461 MW |
| **Prévision J-1 de RTE (la référence à battre)** | **1 428 MW** | **1 395 MW** |

L'erreur de la prévision J-1 de RTE a presque doublé depuis 2022 : environ 800 à 900 MW par an de 2012 à 2021, environ 1 350 à 1 470 MW depuis 2023. Depuis 2023, elle est aussi **inférieure au réalisé 81 % du temps**. C'est soit un biais réel, soit une différence de définition entre la prévision et la consommation définitive (**À VÉRIFIER** avant toute conclusion).

## 4. Les garde-fous

- **Aucune fuite de données.** Seules entrent dans le modèle des informations connues la veille à midi : le calendrier (heure, jour, jours fériés, vacances), les consommations passées, la météo **prévue**. La production par filière, les échanges aux frontières et la prévision J (du jour même) sont publiés en même temps que la consommation : interdits, sauf décalés d'au moins 24 heures. Un test automatique vérifiera qu'aucune variable n'est postérieure à l'heure de décision.
- **La météo réalisée n'est pas la météo prévue.** Entraîner sur les températures observées rendrait le modèle trop optimiste. Soit on utilise des prévisions météo archivées, soit cette limite est écrite et chiffrée (**À TRANCHER** selon les données disponibles).
- **La décision reste humaine.** Le modèle propose une prévision. Le responsable de la prévision et le dispatcher gardent la décision et peuvent l'écarter, par exemple lors d'un événement exceptionnel (grève, canicule hors norme, crise sanitaire).
- **Pas de données personnelles.** Toutes les données sont des agrégats nationaux publics.
- **AI Act.** L'annexe III vise les systèmes d'IA utilisés comme composants de sécurité dans la gestion des infrastructures critiques, dont l'électricité. Un outil d'aide à la prévision, sous contrôle humain, ne semble pas relever de cette catégorie. Ce point sera argumenté dans l'analyse d'écart à l'AI Act du rendu final (**À VÉRIFIER** sur le texte consolidé).

## 5. Les données

- **Source principale** : RTE, *Données éCO₂mix nationales consolidées et définitives*, publiées sur la plateforme ODRE (jeu `eco2mix-national-cons-def`).
- **Licence** : Licence Ouverte v2.0 (Etalab), réutilisation libre avec citation de la source.
- **Période et volume** : du 1er janvier 2012 au 31 août 2026, au pas de 15 minutes, soit 514 272 lignes et 128 567 heures après agrégation, dont 14 heures sans consommation. Données définitives jusqu'à fin 2025, consolidées en 2026.
- **Accès** : téléchargement par script (`make data`, module `src/energie/data.py`), avec une empreinte SHA-256 pour figer la version (`data/README.md`).
- **Données à ajouter** :
  - la **température**, principal moteur de la consommation (chauffage électrique) : source à choisir (**À COMPLÉTER** : Météo-France en open data ou Open-Meteo, avec leur licence) ;
  - le **calendrier** : jours fériés et vacances scolaires (données ouvertes de l'Éducation nationale sur data.gouv.fr).
- **Ce qui manque** : les prévisions météo telles qu'elles étaient connues la veille, la consommation régionale, les événements exceptionnels (grèves, confinements de 2020).

## 6. Le plan

- **Naïf** : la consommation de la même heure une semaine avant (MAE d'environ 3 400 MW).
- **Référence métier** : la prévision J-1 de RTE, déjà dans les données.
- **Meilleur (jalon 2, 29 janvier)** : une régression linéaire (OLS) sur le calendrier, la température et les consommations passées.
- **Lourd (rendu final, février)** : un gradient boosting (LightGBM), comparé à l'OLS avec des intervalles de confiance. La règle de choix du modèle champion sera écrite avant les résultats.
- **Coupe des données (proposition)** : entraînement 2012-2023, validation 2024, test 2025, fermé jusqu'au rendu final. 2020 (confinements) sera traitée à part.
- **Qui fait quoi ** : Thomas Roujou, rôle Modèle ; Thomas Traineau, rôle Revue et IA ; Martin Goy, rôle Données. Les rôles tournent à chaque jalon.

## Ce que le projet ne fait pas

- Il ne prévoit pas la consommation régionale ni locale, seulement le total national.
- Il ne pilote pas le réseau en temps réel : il sert la prévision de la veille, pas les ajustements infrajournaliers.
- Il ne remplace pas le responsable de la prévision : il propose un chiffre que l'humain retient, combine ou écarte.
- Il ne prévoit pas les prix de l'électricité ni la production par filière.

## Les questions posées au commanditaire (réponses supposées, à confirmer)

1. À quelle heure la prévision J-1 doit-elle être publiée ? Réponse supposée : la veille à midi (À VALIDER).
2. Combien coûte un MW sous-estimé par rapport à un MW surestimé ? Pas encore répondu : à estimer à partir des prix de règlement des écarts publiés par RTE (À COMPLÉTER).
3. La prévision J-1 publiée porte-t-elle sur la même définition de consommation que les données définitives ? Pas encore répondu : conditionne l'interprétation du biais observé depuis 2023 (À VÉRIFIER).
4. Quelles prévisions météo étaient disponibles la veille, et peut-on y accéder en archive ? Pas encore répondu (À TRANCHER).

## Qui nous sommes vraiment

> Chaque membre écrit sa propre ligne : parcours, métier visé, pourquoi cette option, centres d'intérêt.

- **Thomas Roujou** : Étudiant en finance de marché spécialisé en structuration de produit dérivés et stratégies systamatique, avec un fort attrait pour le machine learning, je cherche à en apprendre plus sur l'analyse de données et la gestion d'un projet d'analyse automatique.
- **Thomas Traineau** : À COMPLÉTER
- **Martin Goy** : À COMPLÉTER
