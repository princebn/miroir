"""
src/synth/compatibility.py

Règles métier pour la compatibilité cliente × article. Chaque mapping
est une constante auditable et documentée dans data/synthetic/spec.md.

Trois axes scorés :
- Couleur     : 12 sous-saisons Sci\\ART × 46 baseColour de la dataset Fashion
- Occasion    : 6 occasions client × `usage` du dataset Fashion
- Archétype   : 6 archétypes × `articleType` (proxy, documenté comme tel)

Chaque score ∈ [0, 1]. Le score combiné est la moyenne pondérée des trois.
"""
from __future__ import annotations


# ============================================================================
# 1. Mapping COULEUR  ←→  SOUS-SAISON colorimétrique
# Référence : système Sci\ART (12 sous-saisons)
# Tier 1 = couleurs signatures (score 1,0)
# Tier 2 = couleurs compatibles élargies (score 0,6)
# Hors palette = score 0,1
# ============================================================================

SAISON_PALETTES: dict[str, tuple[set[str], set[str]]] = {
    # SPRING family (chaud + clair)
    "printemps_clair": (
        {"Peach", "Coral", "Cream", "Off White", "Beige", "Pink"},
        {"Yellow", "Tan", "Nude", "Skin", "Mauve", "Turquoise Blue"},
    ),
    "printemps_chaud": (
        {"Coral", "Peach", "Orange", "Yellow", "Mustard", "Tan", "Khaki", "Olive", "Beige", "Cream"},
        {"Brown", "Rust", "Gold", "Bronze", "Green", "Red"},
    ),
    "printemps_lumineux": (
        {"Coral", "Pink", "Yellow", "Orange", "Turquoise Blue", "Red", "Magenta"},
        {"Navy Blue", "Green", "Purple", "Black", "White", "Gold", "Teal"},
    ),

    # SUMMER family (froid + doux)
    "ete_doux": (
        {"Rose", "Mauve", "Lavender", "Grey", "Mushroom Brown", "Beige", "Skin", "Steel"},
        {"Pink", "Blue", "Sea Green", "Khaki", "Off White"},
    ),
    "ete_froid": (
        {"Rose", "Pink", "Blue", "Lavender", "Silver", "Grey", "White"},
        {"Mauve", "Steel", "Turquoise Blue", "Navy Blue", "Sea Green", "Burgundy"},
    ),
    "ete_lumineux": (
        {"Pink", "Lavender", "Blue", "Off White", "Silver", "Cream", "Skin"},
        {"Sea Green", "Mauve", "Steel", "Beige"},
    ),

    # AUTUMN family (chaud + profond)
    "automne_chaud": (
        {"Rust", "Mustard", "Olive", "Coffee Brown", "Brown", "Bronze", "Copper", "Khaki", "Tan"},
        {"Burgundy", "Gold", "Beige", "Cream", "Maroon", "Red", "Green"},
    ),
    "automne_profond": (
        {"Burgundy", "Maroon", "Coffee Brown", "Charcoal", "Olive", "Bronze", "Mushroom Brown", "Brown"},
        {"Rust", "Mustard", "Black", "Navy Blue", "Green", "Purple"},
    ),
    "automne_doux": (
        {"Beige", "Tan", "Khaki", "Olive", "Mustard", "Mushroom Brown", "Mauve", "Cream"},
        {"Bronze", "Rust", "Skin", "Coffee Brown", "Steel", "Sea Green"},
    ),

    # WINTER family (froid + contrasté)
    "hiver_froid": (
        {"Red", "Pink", "Magenta", "Navy Blue", "Black", "White", "Charcoal", "Silver"},
        {"Burgundy", "Maroon", "Grey", "Purple", "Blue", "Green"},
    ),
    "hiver_profond": (
        {"Black", "Navy Blue", "Burgundy", "Maroon", "Charcoal", "Purple", "White"},
        {"Red", "Blue", "Green", "Brown", "Grey", "Silver"},
    ),
    "hiver_lumineux": (
        {"White", "Black", "Magenta", "Fluorescent Green", "Blue", "Red", "Turquoise Blue"},
        {"Silver", "Charcoal", "Purple", "Pink", "Yellow", "Green", "Teal"},
    ),
}


def color_score(color: str | None, saison: str) -> float:
    """Score de compatibilité couleur ∈ [0, 1]."""
    if not color or color in {"Multi", "Metallic"}:
        # couleurs neutres / multicolores : compatibilité moyenne par défaut
        return 0.4
    tier1, tier2 = SAISON_PALETTES[saison]
    if color in tier1:
        return 1.0
    if color in tier2:
        return 0.6
    return 0.1


# ============================================================================
# 2. Mapping OCCASION ←→ `usage` Fashion dataset
# Le dataset a : Casual, Formal, Smart Casual, Sports, Party, Travel, Ethnic, Home
# ============================================================================

OCCASION_USAGES: dict[str, set[str]] = {
    "bureau":   {"Formal", "Smart Casual"},
    "cocktail": {"Party", "Formal", "Smart Casual"},
    "vacances": {"Casual", "Travel", "Ethnic"},
    "sport":    {"Sports"},
    "soiree":   {"Party", "Formal"},
    "casual":   {"Casual", "Smart Casual"},
}


def occasion_score(usage: str | None, occasion: str) -> float:
    """Score de compatibilité occasion ∈ [0, 1]."""
    if not usage:
        return 0.3
    return 1.0 if usage in OCCASION_USAGES[occasion] else 0.2


# ============================================================================
# 3. Mapping ARCHÉTYPE ←→ `articleType`
# /!\ Proxy heuristique, pas une vérité absolue.
# Documenté comme tel dans data/synthetic/spec.md.
# Liste articleType (extrait Fashion dataset)
# ============================================================================

ARCHETYPE_ARTICLE_TYPES: dict[str, set[str]] = {
    "classique": {
        "Shirts", "Trousers", "Formal Shoes", "Suits", "Blazers", "Ties",
        "Watches", "Belts", "Wallets",
    },
    "naturel": {
        "Tshirts", "Tops", "Jeans", "Casual Shoes", "Sneakers", "Shorts",
        "Caps", "Backpacks", "Flip Flops",
    },
    "romantique": {
        "Dresses", "Tunics", "Kurtas", "Skirts", "Camisoles", "Sandals",
        "Heels", "Earrings", "Bangle", "Perfume and Body Mist",
    },
    "dramatique": {
        "Jackets", "Coats", "Boots", "Heels", "Sunglasses", "Handbags",
        "Stoles", "Scarves",
    },
    "creatif": {
        "Tshirts", "Sweatshirts", "Track Pants", "Sneakers", "Caps",
        "Handbags", "Scarves", "Watches", "Bracelet",
    },
    "elegant_chic": {
        "Dresses", "Heels", "Handbags", "Watches", "Sunglasses", "Earrings",
        "Necklace and Chains", "Blazers", "Perfume and Body Mist",
    },
}


def archetype_score(article_type: str | None, archetypes: list[str]) -> float:
    """Score de compatibilité archétype ∈ [0, 1].

    Si l'article type matche AU MOINS UN archétype de la cliente, score 1.
    Sinon, fallback à 0,4 (un article neutre n'est pas exclu).
    """
    if not article_type:
        return 0.4
    for arch in archetypes:
        if article_type in ARCHETYPE_ARTICLE_TYPES.get(arch, set()):
            return 1.0
    return 0.4


# ============================================================================
# 4. Score combiné + label
# ============================================================================

W_COLOR = 0.40
W_OCCASION = 0.40
W_ARCHETYPE = 0.20

# Seuil au-dessus duquel un article est "approuvé"
APPROVAL_THRESHOLD = 0.70

# Probabilité qu'un label soit inversé (bruit humain)
LABEL_FLIP_PROB = 0.05


def combined_score(
    color: str | None,
    usage: str | None,
    article_type: str | None,
    saison: str,
    occasion: str,
    archetypes: list[str],
) -> tuple[float, float, float, float]:
    """Retourne (color_s, occasion_s, archetype_s, combined)."""
    cs = color_score(color, saison)
    os_ = occasion_score(usage, occasion)
    as_ = archetype_score(article_type, archetypes)
    combined = W_COLOR * cs + W_OCCASION * os_ + W_ARCHETYPE * as_
    return cs, os_, as_, combined
