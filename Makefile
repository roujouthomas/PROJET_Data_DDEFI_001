# Les cibles du cours. `make reproduce` doit donner deux fois les mêmes chiffres.
export PYTHONPATH := src
PY ?= python

reproduce: data split train metrics

data:            ## télécharge éCO₂mix (RTE), agrège par heure, vérifie l'empreinte
	$(PY) -m energie.data --check data/sha256.txt

split:           ## la coupe figée par années : 2012-2023, 2024, 2025
	$(PY) -m energie.split --config config.yaml

train:           ## le modèle naïf (J-7) et l'OLS
	$(PY) -m energie.model --config config.yaml

metrics:         ## les métriques sur la validation : metrics.json
	$(PY) -m energie.evaluate --config config.yaml --out metrics.json

compare:         ## jalon 2 : les trois modèles sur le test, une seule fois : compare.json
	$(PY) -m energie.compare --config config.yaml --out compare.json

predict:         ## batch : prévoir les heures d'un CSV (voir batch/predict.py)
	$(PY) batch/predict.py --in data/processed/validation.csv --out predictions.csv

test:            ## les tests
	$(PY) -m pytest -q tests/

app:             ## l'interface minimale
	streamlit run app/app.py

clean:
	rm -rf data/processed models/*.pkl metrics.json compare.json predictions.csv

.PHONY: reproduce data split train metrics compare predict test app clean
