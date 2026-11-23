"""Test 2, la coupe figée : toujours les mêmes plis, dans l'ordre du temps.

Les empreintes attendues sont écrites ici en dur : si elles changent, quelqu'un a touché à la
coupe ou aux données, et il doit le dire dans DECISIONS.md avant de mettre ce test à jour.
"""

from energie.split import FOLDS, fold_hash, make_split

EXPECTED = {
    "train": "da956ceca5363d320c7bc25ce11336507675f2d7191129417f3ea65bd94d9bd8",
    "validation": "9f071dc69ff291be56fbf9dbf70d376341594f0e8eaffb8b24d801c0a5abfe1c",
    "test": "308deb1eaddb7df9778aa53f2456c854bfde21ae0a329c02f972a51253a94d0b",
}


def test_split_is_frozen_and_chronological(raw, cfg):
    folds = make_split(raw, cfg)
    sizes = {k: len(v) for k, v in folds.items()}
    assert sizes == {"train": 104_988, "validation": 8_781, "test": 8_757}
    # Chronologique : toute heure d'entraînement précède toute heure de validation, etc.
    assert folds["train"]["date_heure"].max() < folds["validation"]["date_heure"].min()
    assert folds["validation"]["date_heure"].max() < folds["test"]["date_heure"].min()
    for name in FOLDS:
        a0, a1 = cfg["split"][name]
        assert folds[name]["annee"].between(a0, a1).all()
        assert fold_hash(folds[name]) == EXPECTED[name], f"la coupe « {name} » a changé"
