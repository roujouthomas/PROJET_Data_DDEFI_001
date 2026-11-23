"""Batch 1 : préparer. Télécharge éCO₂mix, vérifie l'empreinte, écrit la coupe figée.

    python batch/prepare.py

Équivalent de `make data split`. Les scripts de batch/ enchaînent les modules de src/energie ;
ils ne contiennent pas de logique : si vous écrivez du code ici, c'est qu'il manque dans src/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from energie.config import ROOT, load_config  # noqa: E402
from energie.data import check_hash  # noqa: E402
from energie.split import write_split  # noqa: E402

if __name__ == "__main__":
    cfg = load_config()
    check_hash(ROOT / "data" / "sha256.txt", cfg)
    hashes = write_split(cfg)
    print("coupe écrite :", ", ".join(f"{k} {v[:8]}…" for k, v in hashes.items()))
