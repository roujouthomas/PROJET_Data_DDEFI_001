# Fiche de données (datasheet)

D'après Gebru et al. (2021), « Datasheets for Datasets », en version courte. À compléter au jalon 1.

| Question | Réponse |
|---|---|
| Pourquoi ce jeu a-t-il été constitué ? | RTE publie l'équilibre offre-demande du réseau électrique français (éCO₂mix) : consommation, prévisions, production par filière, échanges. |
| Qui l'a produit, quand ? | RTE, gestionnaire du réseau de transport, de 2012 à aujourd'hui ; diffusé sur la plateforme ODRE. |
| Qu'est-ce qu'une ligne ? | Dans l'export, un quart d'heure ; dans notre fichier de travail, une heure de consommation nationale (France métropolitaine). |
| Combien de lignes, de colonnes ? | Fichier de travail : 122 736 heures (2012-2025) et 3 colonnes (`date_heure`, `consommation`, `prevision_j1`). |
| Comment la cible a-t-elle été obtenue ? | Consommation mesurée par RTE, publiée en temps réel puis consolidée, puis définitive environ un an plus tard. |
| Que manque-t-il ? | 14 heures sans consommation ; pas de température, pas de consommation régionale, pas de trace des événements exceptionnels (grèves, confinements). |
| Qui est sous-représenté ? | Pas de personnes : des agrégats nationaux. Les périodes atypiques (2020, crise énergétique 2022) sont peu nombreuses. À mesurer au jalon 1. |
| Données personnelles ? | Aucune. |
| Peut-on l'utiliser pour autre chose ? | Pas pour une prévision régionale ou locale, ni infrajournalière : le jeu est national et agrégé. |
| Licence | Licence Ouverte v2.0 (Etalab). |
