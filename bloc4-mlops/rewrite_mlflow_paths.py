import sqlite3

OLD = "/Users/prince/Documents/miroir/bloc4-mlops/mlruns"
NEW = "/app/mlruns"

conn = sqlite3.connect("mlflow.db")
cur = conn.cursor()
tables = [
    r[0]
    for r in cur.execute("SELECT name FROM sqlite_master WHERE type = ?", ("table",)).fetchall()
]
total = 0
for t in tables:
    cols = [r[1] for r in cur.execute(f"PRAGMA table_info([{t}])").fetchall()]
    for col in cols:
        try:
            res = cur.execute(
                f"UPDATE [{t}] SET [{col}] = REPLACE([{col}], ?, ?) WHERE [{col}] LIKE ?",
                (OLD, NEW, "%" + OLD + "%"),
            )
            if res.rowcount and res.rowcount > 0:
                total += res.rowcount
        except Exception:
            pass
conn.commit()
conn.close()
print("paths rewritten in mlflow.db, rows touched:", total)
