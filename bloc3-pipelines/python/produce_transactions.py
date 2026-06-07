#!/usr/bin/env python3
"""Miroir Bloc 3 - Producteur : rejoue les vraies transactions H&M dans Kafka.

--stride N : ne prend qu'une ligne sur N (pour etaler l'echantillon sur toute
la plage de dates du fichier, trie par date).
"""
import json, time, argparse, os
from confluent_kafka import Producer

CSV = os.path.expanduser(
    "~/Downloads/h-and-m-personalized-fashion-recommendations/transactions_train.csv")
TOPIC = "miroir.transactions"
COLS = ["t_dat", "customer_id", "article_id", "price", "sales_channel_id"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=int, default=500, help="messages/seconde (0 = max)")
    ap.add_argument("--limit", type=int, default=2000, help="0 = sans limite")
    ap.add_argument("--stride", type=int, default=1, help="1 ligne sur N")
    args = ap.parse_args()

    p = Producer({"bootstrap.servers": "localhost:9092",
                  "client.id": "miroir-producer"})
    sent = 0
    interval = 1.0 / args.rate if args.rate > 0 else 0
    t0 = time.time()
    with open(CSV) as f:
        next(f)  # entete
        for i, line in enumerate(f):
            if args.stride > 1 and i % args.stride != 0:
                continue
            fields = line.rstrip("\n").split(",")
            if len(fields) != 5:
                continue
            row = dict(zip(COLS, fields))
            row["ingested_at"] = round(time.time(), 3)
            p.produce(TOPIC, key=row["customer_id"], value=json.dumps(row))
            sent += 1
            if sent % 500 == 0:
                p.poll(0)
                print(f"  envoyes: {sent}")
            if args.limit and sent >= args.limit:
                break
            if interval:
                time.sleep(interval)
    p.flush()
    dt = time.time() - t0
    print(f"TOTAL: {sent} messages -> {TOPIC} en {dt:.1f}s ({sent/max(dt,0.1):.0f} msg/s)")

if __name__ == "__main__":
    main()
