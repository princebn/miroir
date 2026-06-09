"""
src/common/db.py

Connexion Postgres centralisée. Paramètres lus dans l'environnement,
avec des défauts pour le Postgres local du Bloc 2 (Docker Desktop).

Usage:
    from src.common.db import get_conn
    with get_conn() as conn:
        ...
"""

from __future__ import annotations

import os

import psycopg2
from pgvector.psycopg2 import register_vector

PG_DSN = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432"),
    "dbname": os.environ.get("PGDATABASE", "miroir"),
    "user": os.environ.get("PGUSER", "miroir"),
    "password": os.environ.get("PGPASSWORD", "miroir_local_pwd"),
}


def get_conn(register_pgvector: bool = True):
    """Retourne une connexion psycopg2. Enregistre l'adapter pgvector par défaut."""
    conn = psycopg2.connect(**PG_DSN)
    if register_pgvector:
        register_vector(conn)
    return conn
