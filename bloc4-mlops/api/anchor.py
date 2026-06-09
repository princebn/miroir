"""Style anchor: build a CLIP text embedding from a client's profile + occasion."""

from __future__ import annotations

from typing import List

import numpy as np

_clip_model = None
_clip_tokenizer = None


SAISON_TO_DESCRIPTOR = {
    "printemps_clair": "soft warm pastel",
    "printemps_chaud": "warm clear",
    "printemps_lumineux": "vibrant warm",
    "ete_doux": "muted cool",
    "ete_froid": "cool clear",
    "ete_lumineux": "soft cool pastel",
    "automne_chaud": "rich warm earthy",
    "automne_profond": "deep warm",
    "automne_doux": "muted warm earthy",
    "hiver_froid": "bold cool",
    "hiver_profond": "deep cool",
    "hiver_lumineux": "icy cool",
}

OCCASION_TO_DESCRIPTOR = {
    "bureau": "professional workwear",
    "cocktail": "elegant cocktail",
    "vacances": "relaxed vacation",
    "sport": "athletic sportswear",
    "soiree": "evening party",
    "casual": "casual everyday",
}

ARCHETYPE_TO_DESCRIPTOR = {
    "classique": "classic timeless",
    "naturel": "natural relaxed",
    "romantique": "romantic feminine",
    "dramatique": "dramatic bold",
    "creatif": "creative eclectic",
    "elegant_chic": "elegant chic",
}


def _ensure_clip_loaded():
    global _clip_model, _clip_tokenizer
    if _clip_model is None:
        import open_clip

        _clip_model, _, _ = open_clip.create_model_and_transforms(
            "ViT-B-32",
            pretrained="openai",
            force_quick_gelu=True,
        )
        _clip_model.eval()
        _clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")


def build_query(occasion: str, saison: str, archetypes: List[str]) -> str:
    occ_desc = OCCASION_TO_DESCRIPTOR.get(occasion, occasion)
    sai_desc = SAISON_TO_DESCRIPTOR.get(saison, saison)
    arch = archetypes[0] if archetypes else "classique"
    arch_desc = ARCHETYPE_TO_DESCRIPTOR.get(arch, "classic timeless")
    return f"{occ_desc} outfit in {sai_desc} tones, {arch_desc} style"


def encode_query(query: str) -> np.ndarray:
    import torch

    _ensure_clip_loaded()
    with torch.no_grad():
        tokens = _clip_tokenizer([query])
        feats = _clip_model.encode_text(tokens)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats.cpu().numpy().flatten().astype(np.float32)


def style_anchor_for_client(occasion: str, saison: str, archetypes: List[str]) -> np.ndarray:
    return encode_query(build_query(occasion, saison, archetypes))
