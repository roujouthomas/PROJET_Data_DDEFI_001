"""Les tests importent src/energie sans installation : on ajoute src/ au chemin."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from energie.config import load_config  # noqa: E402
from energie.data import load_raw  # noqa: E402


@pytest.fixture(scope="session")
def cfg():
    return load_config("config.yaml")


@pytest.fixture(scope="session")
def raw(cfg):
    return load_raw(cfg)
