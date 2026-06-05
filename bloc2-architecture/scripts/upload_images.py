import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from tqdm import tqdm
from config import settings

IMG_DIR = os.path.expanduser("~/Downloads/archive fashion/images")
BUCKET = settings.minio_bucket

s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.minio_endpoint}",
    aws_access_key_id=settings.minio_access_key,
    aws_secret_access_key=settings.minio_secret_key,
    config=Config(signature_version="s3v4", max_pool_connections=64),
    region_name="us-east-1",
)

def ensure_bucket():
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)
        print(f"bucket cree: {BUCKET}")

def list_existing():
    existing = set()
    p = s3.get_paginator("list_objects_v2")
    for page in p.paginate(Bucket=BUCKET, Prefix="products/"):
        for obj in page.get("Contents", []):
            existing.add(obj["Key"].split("/")[-1])
    return existing

def upload_one(fname):
    s3.upload_file(os.path.join(IMG_DIR, fname), BUCKET, f"products/{fname}")
    return fname

def main():
    ensure_bucket()
    files = [f for f in os.listdir(IMG_DIR) if f.endswith(".jpg")]
    existing = list_existing()
    todo = [f for f in files if f not in existing]
    print(f"images locales: {len(files)} | deja presentes: {len(existing)} | a uploader: {len(todo)}")
    with ThreadPoolExecutor(max_workers=32) as ex:
        futures = {ex.submit(upload_one, f): f for f in todo}
        for _ in tqdm(as_completed(futures), total=len(todo)):
            pass
    total = 0
    p = s3.get_paginator("list_objects_v2")
    for page in p.paginate(Bucket=BUCKET, Prefix="products/"):
        total += len(page.get("Contents", []))
    print(f"objets dans bucket {BUCKET}: {total}")

if __name__ == "__main__":
    main()
