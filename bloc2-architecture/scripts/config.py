import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

class Settings:
    database_url = os.environ["DATABASE_URL"]
    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key = os.environ.get("MINIO_ROOT_USER", "miroir_admin")
    minio_secret_key = os.environ.get("MINIO_ROOT_PASSWORD", "miroir_minio_pwd")
    minio_bucket = os.environ.get("MINIO_BUCKET", "miroir-products")

settings = Settings()
