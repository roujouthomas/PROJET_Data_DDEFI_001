# Cahier des charges : Watt Data Conseil × RTE, prévision de la consommation électrique

> Jalon 1, projet data DDEFI 2026-2027, Centrale Méditerranée, groupe 8.
> Équipe : Thomas Roujou, Thomas Traineau, Martin Goy.
> Les décisions et leurs alternatives rejetées sont datées dans `DECISIONS.md`.

## La persona : qui nous incarnons

Nous sommes **Watt Data Conseil**, un cabinet de conseil en données (fictif). Nous sommes mandatés par **la direction en charge de l'équilibre offre-demande de RTE**, le gestionnaire du réseau de transport d'électricité français. RTE doit garantir à chaque instant que la production égale la consommation. Pour cela, il s'appuie la veille sur une prévision de la consommation du lendemain, qui sert à dimensionner les marges et les réserves.

Notre interlocuteur est **le responsable de la prévision de consommation**. C'est lui qui valide la méthode et signe la mise en service d'un nouveau modèle. Le **dispatcher** du centre de conduite garde la décision opérationnelle finale.

## La question en une phrase

> Chaque veille, quelle consommation horaire nationale le responsable de la prévision de RTE doit-il retenir pour le lendemain, afin de **réduire l'erreur de prévision par rapport à la prévision J-1 actuelle**, dégradée depuis 2022, et donc **le volume de réserves activées en urgence** ?

| Marqueur | Dans notre question |
|---|---|
| Une décision | la consommation horaire retenue la veille pour le lendemain, qui fixe le niveau de marges et de réserves programmées |
| Une mesure | l'erreur absolue moyenne en MW par rapport au réalisé, et le coût des écarts qui en découle |
| Un périmètre | la France métropolitaine, les 24 heures du lendemain, chaque jour |
| Un responsable | le responsable de la prévision de consommation de RTE, qui signe ; le dispatcher, qui décide en temps réel |

## En six lignes

| Ligne | Réponse |
|---|---|
| **La décision servie** | Chaque veille à midi, le responsable de la prévision de RTE retient la consommation attendue pour les 24 heures du lendemain, qui fixe les marges et réserves programmées. |
| **La cible** | `consommation` : consommation nationale réalisée, moyenne horaire en MW, horizon de 12 à 36 heures. |
| **La métrique** | Pour le décideur : un coût asymétrique des écarts (sous-estimer coûte plus cher). Pour l'ingénieur : MAE en MW et en %, erreur moyenne signée. Seuil d'utilité : battre la prévision J-1 de RTE, brute et corrigée de son écart moyen. |
| **Les données** | RTE éCO₂mix national définitif 2012-2025 (ODRE, Licence Ouverte v2.0), téléchargé par script avec empreinte SHA-256 ; température Open-Meteo (CC BY 4.0) ; calendrier des jours fériés calculé. |
| **Les garde-fous** | Uniquement des informations connues la veille à midi (retards d'au moins 36 h) ; production, échanges et prévisions RTE jamais en variables ; évaluation avec la météo prévue la veille ; décision humaine ; aucune donnée personnelle ; position AI Act à argumenter. |
| **Le plan** | Naïf : même heure une semaine avant. Meilleur (jalon 2, 29 janvier) : OLS sur le calendrier, la température et les consommations passées. Lourd (rendu final) : XGBoost, comparé à l'OLS avec intervalles de confiance. Coupe chronologique : 2012-2023, 2024, 2025. |

Le détail de chaque ligne suit.

## 1. La décision

**Qui et quand.** La veille du jour J, à midi, le responsable de la prévision publie la consommation attendue pour chacune des 24 heures de J. Cette prévision fixe le volume de marges et de réserves que RTE programme pour J. L'heure de midi est un choix de conception : elle laisse le temps de programmer les moyens du lendemain, et elle fixe la règle anti-fuite (une consommation n'est connue que si elle a au moins 36 heures au moment de prévoir 23 h le jour J).

**Les options.** Retenir notre prévision, garder la prévision J-1 actuelle, ou combiner les deux.

**Ce que coûte chaque erreur.** Les deux erreurs n'ont pas le même prix :

- **Sous-estimer la consommation** (prévoir moins que le réalisé). RTE doit activer en urgence des moyens d'ajustement, souvent des centrales de pointe au gaz, au prix fort. Dans le pire cas, l'équilibre du réseau est menacé. C'est l'erreur la plus coûteuse.
- **Surestimer la consommation** (prévoir plus que le réalisé). RTE a réservé de la capacité qui ne sert pas. Le coût est réel, mais plus faible.

Le rapport exact entre ces deux coûts sera estimé au jalon 2 à partir des prix de règlement des écarts publiés par RTE (**À COMPLÉTER**). D'ici là, il n'est pas chiffré dans `config.yaml` : on n'invente pas de nombre.

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
| **Prévision J-1 de RTE, brute** | **1 428 MW** | **1 395 MW** |
| **Prévision J-1 de RTE, corrigée de son écart moyen de l'année précédente** | **1 039 MW** | **1 120 MW** |

**Le biais de RTE, vérifié.** Depuis 2023, la prévision J-1 de RTE est inférieure au réalisé environ 80 % du temps, de 1 131 MW en moyenne en 2023 et de 1 146 MW en 2024. Trois constats montrent qu'il s'agit d'un **décalage systématique**, probablement une différence de définition entre la consommation prévue et la consommation publiée, et non d'erreurs de prévision au sens propre :

1. la prévision **du jour même** (J) a le même écart moyen que la prévision de la veille (−1 142 MW en 2023, −1 167 MW en 2024), alors qu'une prévision faite quelques heures avant ne devrait pas se tromper d'un gigawatt dans le même sens toute l'année ;
2. l'écart est présent à chaque trimestre de 2023 à 2026 ;
3. il existe aussi dans les données consolidées de 2026, donc il ne vient pas de la révision des données définitives.

Conséquence pour nous : un modèle entraîné sur la consommation publiée évite ce décalage sans effort, ce qui le ferait gagner contre la prévision brute pour une mauvaise raison. Nous comparerons donc toujours aussi à la **prévision RTE corrigée** de l'écart moyen de l'année précédente, ce qui n'utilise que des informations passées. La vraie barre est **1 039 MW en 2024**. Même en retirant l'écart moyen de chaque année, l'erreur de RTE a augmenté depuis 2022 (entre 710 et 890 MW par an de 2012 à 2021, 965 MW en 2023, 1 039 MW en 2024) : la dégradation est réelle, mais plus faible qu'il n'y paraît. La cause exacte du décalage reste une question pour le commanditaire (question 3 ci-dessous).

## 4. Les garde-fous

- **Aucune fuite de données.** Seules entrent dans le modèle des informations connues la veille à midi : le calendrier (heure, type de jour, mois, jours fériés), les consommations passées d'au moins 36 heures (même heure à J-2 et à J-7), la météo. La production par filière, les échanges aux frontières et les prévisions de RTE ne sont jamais des variables. `tests/test_leakage.py` vérifie qu'aucune variable ne bouge quand on modifie les 36 dernières heures de données.
- **La météo réalisée n'est pas la météo prévue.** Les prévisions météo archivées n'existent pas avant 2021 environ : on entraîne donc sur la température observée, puis on **évalue 2024 et 2025 deux fois**, avec la température observée et avec la température prévue la veille. L'écart entre les deux chiffre ce que coûte l'erreur de la météo, et c'est le second chiffre qui compte pour le décideur.
- **La décision reste humaine.** Le modèle propose une prévision. Le responsable de la prévision et le dispatcher gardent la décision et peuvent l'écarter, par exemple lors d'un événement exceptionnel (grève, canicule hors norme, crise sanitaire).
- **Pas de données personnelles.** Toutes les données sont des agrégats nationaux publics.
- **AI Act.** L'annexe III vise les systèmes d'IA utilisés comme composants de sécurité dans la gestion des infrastructures critiques, dont l'électricité. Un outil d'aide à la prévision, sous contrôle humain, ne semble pas relever de cette catégorie. Ce point sera argumenté dans l'analyse d'écart à l'AI Act du rendu final (**À VÉRIFIER** sur le texte consolidé).

## 5. Les données

- **Source principale** : RTE, *Données éCO₂mix nationales consolidées et définitives*, publiées sur la plateforme ODRE (jeu `eco2mix-national-cons-def`), Licence Ouverte v2.0 (Etalab).
- **Ce qu'on garde** : les données **définitives** du 1er janvier 2012 au 31 décembre 2025, soit 122 736 heures après agrégation, dont 14 sans consommation. Les données consolidées de 2026 sont écartées : RTE les révise encore, elles feraient changer l'empreinte.
- **Accès** : téléchargement par script (`make data`, module `src/energie/data.py`), avec une empreinte SHA-256 pour figer la version (`data/README.md`).
- **Température** : **Open-Meteo**, licence CC BY 4.0, sans clé pour un usage non commercial.
  - pour l'entraînement : la température horaire observée (réanalyse ERA5) de 2012 à 2025 ;
  - pour l'évaluation : les prévisions de la veille archivées (Previous Runs API), disponibles en 2024 et 2025 ;
  - une température « France » : moyenne de grandes villes pondérée par leur population ;
  - les données de stations de Météo-France (data.gouv.fr, Licence Ouverte) servent de contrôle.
- **Calendrier** : les onze jours fériés nationaux, calculés dans le code (Pâques par l'algorithme de Meeus). Les vacances scolaires (data.gouv.fr) seront ajoutées au jalon 2.
- **Ce qui manque** : la consommation régionale, les événements exceptionnels (grèves, confinements de 2020), les prévisions météo archivées avant 2021.

## 6. Le plan

- **Naïf** : la consommation de la même heure une semaine avant. MAE de 3 247 MW en 2024.
- **Référence métier** : la prévision J-1 de RTE, brute et corrigée de son écart moyen de l'année précédente (section 3).
- **Meilleur (jalon 2, 29 janvier)** : une régression linéaire (OLS) sur le calendrier (heure croisée avec le type de jour, mois), la température (en degrés de chauffage) et les consommations à J-2 et J-7. Sans température, elle fait déjà 2 388 MW en 2024 (`metrics.json`).
- **Lourd (rendu final, février)** : un XGBoost sur les mêmes variables, hyperparamètres choisis par validation croisée temporelle sur l'entraînement seulement, comparé à l'OLS avec des intervalles de confiance. La règle de choix du modèle champion sera écrite dans `DECISIONS.md` avant de lire le test.
- **Coupe des données** : entraînement 2012-2023, validation 2024, test 2025, fermé jusqu'au rendu final. 2020 (confinements) reste dans l'entraînement ; son effet sera mesuré au jalon 2 en réentraînant sans elle.
- **Qui fait quoi** : Thomas Roujou, rôle Modèle ; Thomas Traineau, rôle Revue et IA ; Martin Goy, rôle Données. Les rôles tournent à chaque jalon.

## Ce que le projet ne fait pas

- Il ne prévoit pas la consommation régionale ni locale, seulement le total national.
- Il ne pilote pas le réseau en temps réel : il sert la prévision de la veille, pas les ajustements infrajournaliers.
- Il ne remplace pas le responsable de la prévision : il propose un chiffre que l'humain retient, combine ou écarte.
- Il ne prévoit pas les prix de l'électricité ni la production par filière.

## Les questions posées au commanditaire (réponses supposées, à confirmer)

1. À quelle heure la prévision J-1 doit-elle être publiée ? Réponse retenue : la veille à midi (section 1).
2. Combien coûte un MW sous-estimé par rapport à un MW surestimé ? À estimer au jalon 2 à partir des prix de règlement des écarts publiés par RTE.
3. Pourquoi la prévision J-1 et la prévision J sont-elles environ 1 100 MW sous la consommation publiée depuis 2023 ? Nos données montrent un décalage systématique (section 3) ; seule RTE peut en donner la cause.
4. Quelles prévisions météo étaient disponibles la veille ? Réponse retenue : les prévisions archivées d'Open-Meteo pour 2024 et 2025, la température observée avant (section 4).

## Qui nous sommes vraiment

> Chaque membre écrit sa propre ligne : parcours, métier visé, pourquoi cette option, centres d'intérêt.

- **Thomas Roujou** : Étudiant en finance de marché spécialisé en structuration de produits dérivés et stratégies systématiques, avec un fort attrait pour le machine learning, je cherche à en apprendre plus sur l'analyse de données et la gestion d'un projet d'analyse automatique.
- **Thomas Traineau** : À COMPLÉTER
- **Martin Goy** : Étudiant en finance de marché, je souhaite m'orienter vers la structuration après une première expérience sur les marchés de taux ; j'ai choisi cette option pour maîtriser les outils d'analyse de données et de machine learning qui deviennent incontournables pour comprendre et anticiper les marchés.
