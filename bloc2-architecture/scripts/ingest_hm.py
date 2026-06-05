import os
import psycopg2
from config import settings

HM = os.path.expanduser("~/Downloads/h-and-m-personalized-fashion-recommendations")
DSN = settings.database_url.replace("postgresql+psycopg2", "postgresql")

def copy_via_staging(cur, csv_path, staging_ddl, staging_table, insert_sql):
    cur.execute(f"DROP TABLE IF EXISTS {staging_table};")
    cur.execute(staging_ddl)
    with open(csv_path, "r", encoding="utf-8") as f:
        cur.copy_expert(f"COPY {staging_table} FROM STDIN WITH (FORMAT csv, HEADER true)", f)
    cur.execute(insert_sql)
    cur.execute(f"DROP TABLE {staging_table};")

def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("TRUNCATE signals.hm_transactions, signals.hm_customers, signals.hm_articles;")
    conn.commit()

    print("articles...")
    copy_via_staging(cur, os.path.join(HM, "articles.csv"),
        """CREATE TEMP TABLE stg_articles (
            article_id text, product_code text, prod_name text, product_type_no text,
            product_type_name text, product_group_name text, graphical_appearance_no text,
            graphical_appearance_name text, colour_group_code text, colour_group_name text,
            perceived_colour_value_id text, perceived_colour_value_name text,
            perceived_colour_master_id text, perceived_colour_master_name text,
            department_no text, department_name text, index_code text, index_name text,
            index_group_no text, index_group_name text, section_no text, section_name text,
            garment_group_no text, garment_group_name text, detail_desc text);""",
        "stg_articles",
        """INSERT INTO signals.hm_articles
           (article_id, product_code, prod_name, product_type_name, product_group_name,
            colour_group_name, department_name, index_name, garment_group_name, detail_desc)
           SELECT article_id, product_code, prod_name, product_type_name, product_group_name,
            colour_group_name, department_name, index_name, garment_group_name, detail_desc
           FROM stg_articles;""")
    conn.commit()

    print("customers...")
    copy_via_staging(cur, os.path.join(HM, "customers.csv"),
        """CREATE TEMP TABLE stg_customers (
            customer_id text, fn text, active text, club_member_status text,
            fashion_news_frequency text, age text, postal_code text);""",
        "stg_customers",
        """INSERT INTO signals.hm_customers
           (customer_id, active, club_member_status, fashion_news_frequency, age, postal_code)
           SELECT customer_id, NULLIF(active,'')::numeric::smallint, club_member_status,
                  fashion_news_frequency, NULLIF(age,'')::numeric::smallint, postal_code
           FROM stg_customers;""")
    conn.commit()

    print("transactions (31M, COPY direct, patiente)...")
    with open(os.path.join(HM, "transactions_train.csv"), "r", encoding="utf-8") as f:
        cur.copy_expert(
            "COPY signals.hm_transactions (t_dat, customer_id, article_id, price, sales_channel_id) "
            "FROM STDIN WITH (FORMAT csv, HEADER true)", f)
    conn.commit()

    for t in ["signals.hm_articles", "signals.hm_customers", "signals.hm_transactions"]:
        cur.execute(f"SELECT count(*) FROM {t};")
        print(t, cur.fetchone()[0])
    cur.close(); conn.close()

if __name__ == "__main__":
    main()
