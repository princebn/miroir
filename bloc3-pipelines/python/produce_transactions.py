#!/usr/bin/env python3
"""Miroir Bloc 3 - Producteur : rejoue les vraies transactions H&M dans Kafka."""
import csv, json, time, argparse, os
from confluent_kafka import Producer

CSV = os.path.expanduser(
    "~/Downloads/h-and-m-personalized-fashion-recommendations/transactions_train.csv")
TOPIC = "miroir.transactions"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=int, default=500)
    ap.add_argument("--limit", type=int, default=2000)
    args = ap.parse_args()
    p = Producer({"bootstrap.servers": "localhost:9092", "client.id": "miroir-producer"})
    sent = 0
    interval = 1.0 / args.rate if args.rate > 0 else 0
    t0 = time.time()
    with open(CSV, newline="") as f:
        for row in csv.DictReader(f):
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
    print(f"TOTAL: {sent} messages -> {TOPIC} en {dt:.1f}s ({sent/dt:.0f} msg/s)")

if __name__ == "__main__":
    main()
