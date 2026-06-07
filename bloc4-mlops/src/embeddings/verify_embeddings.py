"""
src/embeddings/verify_embeddings.py

Vérifie l'état de la table catalog.item_embeddings après ingestion :
- volume total
- répartition par catégorie maître
- exemple de recherche de similarité (cosine) sur un article aléatoire

Usage:
    python src/embeddings/verify_embeddings.py
"""
from __future__ import annotations

from src.common.db import get_conn


def main() -> None:
    conn = get_conn()
    with conn.cursor() as cur:
        # 1. Volume
        cur.execute("SELECT COUNT(*) FROM catalog.item_embeddings")
        total = cur.fetchone()[0]
        print(f"Embeddings en base : {total:,}\n")

        if total == 0:
            print("Table vide. Lance d'abord embed_catalog.py.")
            conn.close()
            return

        # 2. Répartition par master_category
        cur.execute("""
            SELECT COALESCE(master_category, '(null)'), COUNT(*)
            FROM catalog.item_embeddings
            GROUP BY master_category
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        print("Top 10 master_category :")
        for cat, n in cur.fetchall():
            print(f"  {n:>6,}  {cat}")
        print()

        # 3. Exemple de recherche par similarité
        cur.execute("""
            SELECT item_id, embedding, product_display_name, master_category, base_colour
            FROM catalog.item_embeddings
            WHERE product_display_name IS NOT NULL
            ORDER BY random()
            LIMIT 1
        """)
        seed_id, seed_emb, seed_name, seed_cat, seed_col = cur.fetchone()
        print(f"Seed : {seed_id}")
        print(f"  → {seed_name}  [{seed_cat} / {seed_col}]\n")

        # Cosine distance avec pgvector : <=>
        # Similarité cosine = 1 - distance
        cur.execute("""
            SELECT item_id,
                   product_display_name,
                   master_category,
                   base_colour,
                   1 - (embedding <=> %s) AS similarity
            FROM catalog.item_embeddings
            WHERE item_id != %s
            ORDER BY embedding <=> %s
            LIMIT 5
        """, (seed_emb, seed_id, seed_emb))

        print("Top 5 voisins (similarité cosine) :")
        for iid, name, cat, col, sim in cur.fetchall():
            print(f"  {sim:.3f}  {iid}  [{cat} / {col}]  {name}")

    conn.close()


if __name__ == "__main__":
    main()
