#!/usr/bin/env python3
"""Miroir Bloc 3 - Consommateur : charge le flux Kafka dans Postgres."""
import json, time
from confluent_kafka import Consumer
import psycopg2
from psycopg2.extras import execute_values

DSN = "host=localhost port=5432 dbname=miroir user=miroir password=miroir_local_pwd"
TOPIC = "miroir.transactions"
BATCH = 500
IDLE_STOP = 5.0

DDL = """
CREATE TABLE IF NOT EXISTS signals.stream_transactions (
  id               BIGSERIAL PRIMARY KEY,
  t_dat            DATE,
  customer_id      TEXT,
  article_id       BIGINT,
  price            DOUBLE PRECISION,
  sales_channel_id INT,
  ingested_at      DOUBLE PRECISION,
  kafka_partition  INT,
  kafka_offset     BIGINT,
  loaded_at        TIMESTAMPTZ DEFAULT now()
);
"""

def flush(cur, rows):
    if not rows:
        return 0
    execute_values(cur,
        "INSERT INTO signals.stream_transactions "
        "(t_dat, customer_id, article_id, price, sales_channel_id, "
        "ingested_at, kafka_partition, kafka_offset) VALUES %s", rows)
    return len(rows)

def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(DDL)
    conn.commit()
    c = Consumer({"bootstrap.servers": "localhost:9092",
                  "group.id": "miroir-loader",
                  "auto.offset.reset": "earliest",
                  "enable.auto.commit": False})
    c.subscribe([TOPIC])
    rows, total, last = [], 0, time.time()
    try:
        while True:
            msg = c.poll(1.0)
            if msg is None:
                if time.time() - last > IDLE_STOP:
                    break
                continue
            if msg.error():
                continue
            d = json.loads(msg.value())
            rows.append((d["t_dat"], d["customer_id"], int(d["article_id"]),
                         float(d["price"]), int(d["sales_channel_id"]),
                         d.get("ingested_at"), msg.partition(), msg.offset()))
            last = time.time()
            if len(rows) >= BATCH:
                total += flush(cur, rows); conn.commit()
                c.commit(asynchronous=False); rows = []
                print(f"  charges: {total}")
        total += flush(cur, rows); conn.commit()
    finally:
        c.close()
    cur.execute("SELECT count(*) FROM signals.stream_transactions")
    n = cur.fetchone()[0]
    print(f"TOTAL charge cette session: {total}")
    print(f"signals.stream_transactions en base: {n}")
    cur.close(); conn.close()

if __name__ == "__main__":
    main()
