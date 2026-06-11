"""Routes de demonstration pour l'interface Miroir.

- /clients : un extrait du portefeuille de clientes (profils synthetiques).
- /images/{item_id} : sert les visuels du catalogue Fashion en local.

Ces routes existent pour la demo produit ; elles ne font pas partie du
contrat de serving ML (/recommend, /feedback, /health).
"""

import os
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from psycopg2.extras import RealDictCursor

from api.retrieval import CATALOG_TABLE, _pg

router = APIRouter()

_BASE = Path(__file__).resolve().parent.parent
_PROFILES_PATH = Path(
    os.environ.get(
        "MIROIR_PROFILES_PATH",
        str(_BASE / "data" / "synthetic" / "profiles.parquet"),
    )
)
_IMAGES_DIR = Path(
    os.environ.get(
        "MIROIR_IMAGES_DIR",
        str(Path.home() / "Downloads" / "archive fashion" / "images"),
    )
)


@router.get("/clients")
def list_clients(limit: int = 8) -> list[dict]:
    """Renvoie les premiers profils clientes pour le selecteur de l'interface."""
    if not _PROFILES_PATH.exists():
        raise HTTPException(status_code=503, detail="profils indisponibles")
    df = pd.read_parquet(_PROFILES_PATH).head(limit)
    clients = []
    for _, row in df.iterrows():
        clients.append(
            {
                "client_id": str(row["client_id"]),
                "morphologie": str(row["morphologie"]),
                "saison_colorimetrique": str(row["saison_colorimetrique"]),
                "archetypes": [str(a) for a in row["archetypes"]],
                "taille": str(row["taille"]),
            }
        )
    return clients


@router.get("/images/{item_id}")
def get_image(item_id: str) -> FileResponse:
    """Sert l'image d'un article du catalogue (id numerique uniquement)."""
    if not item_id.isdigit():
        raise HTTPException(status_code=400, detail="item_id invalide")
    path = _IMAGES_DIR / f"{item_id}.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="image introuvable")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/similar/{item_id}")
def similar_items(item_id: str, limit: int = 4) -> list[dict]:
    """Voisines visuelles d'un article (cosinus pgvector sur embeddings CLIP)."""
    if not item_id.isdigit():
        raise HTTPException(status_code=400, detail="item_id invalide")
    limit = max(1, min(limit, 12))
    with _pg() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            f"SELECT 1 FROM {CATALOG_TABLE} WHERE item_id::text = %s",
            (item_id,),
        )
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="article introuvable")
        cur.execute(
            f"""
            SELECT item_id::text AS item_id, article_type, base_colour, usage,
                   product_display_name
            FROM {CATALOG_TABLE}
            WHERE embedding IS NOT NULL AND item_id::text <> %s
            ORDER BY embedding <=> (
                SELECT embedding FROM {CATALOG_TABLE} WHERE item_id::text = %s
            )
            LIMIT %s
            """,
            (item_id, item_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]
