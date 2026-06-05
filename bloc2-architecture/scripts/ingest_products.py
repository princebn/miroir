import os
import pandas as pd
from sqlalchemy import create_engine, text
from config import settings

CSV = os.path.expanduser("~/Downloads/archive fashion/styles.csv")

RENAME = {
    "masterCategory": "master_category",
    "subCategory": "sub_category",
    "articleType": "article_type",
    "baseColour": "base_colour",
    "productDisplayName": "display_name",
    "id": "product_id",
}
COLS = ["product_id","gender","master_category","sub_category","article_type",
        "base_colour","season","year","usage","display_name","image_path"]

def main():
    df = pd.read_csv(CSV, on_bad_lines="skip")
    n_raw = len(df)
    df = df.rename(columns=RENAME)
    df["image_path"] = "products/" + df["product_id"].astype(str) + ".jpg"
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df[COLS]

    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE catalog.products RESTART IDENTITY CASCADE;"))
    df.to_sql("products", engine, schema="catalog",
              if_exists="append", index=False, method="multi", chunksize=1000)
    with engine.connect() as conn:
        n_db = conn.execute(text("SELECT count(*) FROM catalog.products")).scalar()
    print(f"styles.csv lignes valides lues: {n_raw}")
    print(f"catalog.products inseres: {n_db}")

if __name__ == "__main__":
    main()
