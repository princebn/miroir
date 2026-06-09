"""
src/synth/generate_profiles.py

Génère N profils clients synthétiques pour Miroir.

Spec auditable    : data/synthetic/spec.md
Sortie             : data/synthetic/profiles.parquet
Reproductibilité   : seed fixe (par défaut 42)

Usage:
    python -m src.synth.generate_profiles
    # ou
    cd bloc4-mlops && python src/synth/generate_profiles.py
"""

from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================================
# Vocabulaires & distributions
# Toute modification ici DOIT être reflétée dans data/synthetic/spec.md
# ============================================================================

MORPHOLOGIES = ["sablier", "rectangle", "triangle", "triangle_inverse", "ovale"]
MORPHOLOGIE_WEIGHTS = [0.35, 0.25, 0.22, 0.10, 0.08]

SAISONS = [
    "printemps_clair",
    "printemps_chaud",
    "printemps_lumineux",
    "ete_doux",
    "ete_froid",
    "ete_lumineux",
    "automne_chaud",
    "automne_profond",
    "automne_doux",
    "hiver_froid",
    "hiver_profond",
    "hiver_lumineux",
]
SAISON_WEIGHTS = [1.0 / 12] * 12  # uniforme

ARCHETYPES = ["classique", "naturel", "romantique", "dramatique", "creatif", "elegant_chic"]
ARCHETYPE_COUNT_WEIGHTS = {1: 0.60, 2: 0.30, 3: 0.10}

BUDGETS = ["bas", "milieu_bas", "milieu_haut", "premium"]
BUDGET_WEIGHTS = [0.20, 0.45, 0.25, 0.10]

OCCASIONS = ["bureau", "cocktail", "vacances", "sport", "soiree", "casual"]
OCCASION_COUNT_WEIGHTS = {1: 0.30, 2: 0.50, 3: 0.20}

TAILLES = ["XS", "S", "M", "L", "XL"]
TAILLE_WEIGHTS = [0.08, 0.25, 0.38, 0.22, 0.07]


# ============================================================================
# Helpers
# ============================================================================


def _sample_multi(
    rng: np.random.Generator,
    values: list[str],
    count_weights: dict[int, float],
) -> list[str]:
    """Échantillonne 1 à N valeurs sans remise, avec distribution donnée du N."""
    counts = list(count_weights.keys())
    weights = list(count_weights.values())
    n = int(rng.choice(counts, p=weights))
    return list(rng.choice(values, size=n, replace=False))


def _new_uuid(rng: np.random.Generator) -> str:
    """UUID4 déterministe (dérivé du RNG seedé, sur 16 octets)."""
    return str(uuid.UUID(bytes=rng.bytes(16)))


# ============================================================================
# Génération
# ============================================================================


def generate_profiles(
    n_consultantes: int = 50,
    clients_per_consultante: int = 30,
    seed: int = 42,
) -> pd.DataFrame:
    """Génère un DataFrame de profils clients synthétiques.

    Args:
        n_consultantes: nombre de consultantes simulées.
        clients_per_consultante: nombre de clientes par consultante.
        seed: graine RNG pour la reproductibilité.

    Returns:
        DataFrame avec colonnes conformes à data/synthetic/spec.md.
    """
    rng = np.random.default_rng(seed)

    consultante_ids = [_new_uuid(rng) for _ in range(n_consultantes)]

    rows = []
    for consultante_id in consultante_ids:
        for _ in range(clients_per_consultante):
            rows.append(
                {
                    "client_id": _new_uuid(rng),
                    "consultante_id": consultante_id,
                    "morphologie": str(rng.choice(MORPHOLOGIES, p=MORPHOLOGIE_WEIGHTS)),
                    "saison_colorimetrique": str(rng.choice(SAISONS, p=SAISON_WEIGHTS)),
                    "archetypes": _sample_multi(rng, ARCHETYPES, ARCHETYPE_COUNT_WEIGHTS),
                    "budget_tranche": str(rng.choice(BUDGETS, p=BUDGET_WEIGHTS)),
                    "occasions": _sample_multi(rng, OCCASIONS, OCCASION_COUNT_WEIGHTS),
                    "taille": str(rng.choice(TAILLES, p=TAILLE_WEIGHTS)),
                }
            )

    return pd.DataFrame(rows)


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    df = generate_profiles()
    out = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "profiles.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)

    print(f"OK — {len(df)} profils écrits dans {out}")
    print()
    print("Aperçu (5 premiers) :")
    print(df.head().to_string())
    print()
    print("Distributions observées (vérifient la spec) :")
    print("  morphologie       :", df.morphologie.value_counts(normalize=True).round(3).to_dict())
    print(
        "  saison (10 prem.) :",
        dict(list(df.saison_colorimetrique.value_counts(normalize=True).round(3).items())[:10]),
    )
    print(
        "  budget            :", df.budget_tranche.value_counts(normalize=True).round(3).to_dict()
    )
    print("  taille            :", df.taille.value_counts(normalize=True).round(3).to_dict())
    print(
        "  archétypes (n)    :",
        df.archetypes.apply(len).value_counts(normalize=True).round(3).to_dict(),
    )
    print(
        "  occasions  (n)    :",
        df.occasions.apply(len).value_counts(normalize=True).round(3).to_dict(),
    )


if __name__ == "__main__":
    main()
