# Les données

- **Source** : RTE, « Données éCO₂mix nationales consolidées et définitives », plateforme ODRE (Open Data Réseaux Énergies), jeu `eco2mix-national-cons-def`.
- **Licence** : Licence Ouverte v2.0 (Etalab). Réutilisation libre, avec citation de la source.
- **Ce qu'on garde** : les données définitives du 1er janvier 2012 au 31 décembre 2025 (heure de Paris), colonnes `date_heure`, `consommation` et `prevision_j1`. Les données consolidées de l'année en cours sont exclues : RTE les révise encore.
- **Téléchargement** : `make data` (module `src/energie/data.py`). Rien n'est versionné dans `data/raw/`.
- **Fichiers produits** :
  - `data/raw/eco2mix_definitif_15min.csv` : l'export ODRE au pas de 15 minutes ;
  - `data/raw/eco2mix_horaire.csv` : la moyenne horaire, une ligne par heure (122 736 heures, dont 14 sans consommation), horodatée en UTC.
- **Empreinte** : `data/sha256.txt` contient le SHA-256 du fichier horaire. On hache le fichier horaire plutôt que l'export brut, parce que la forme de l'export (ordre des colonnes, guillemets) peut changer sans que les chiffres changent. Si l'empreinte change, `make reproduce` s'arrête : écrire pourquoi dans `DECISIONS.md` avant de la mettre à jour.
