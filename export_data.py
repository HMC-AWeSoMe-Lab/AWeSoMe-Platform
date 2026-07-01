import sqlite3
import csv
import os

db_path = os.path.expanduser("~/AWeSoMe-Platform/backend/database/database.db")
conn = sqlite3.connect(db_path)

tables = ["posts", "trial_mode", "questionnaire_responses"]

for table in tables:
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    headers = [desc[0] for desc in conn.execute(f"SELECT * FROM {table}").description]
    with open(f"{table}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Have exported {len(rows)} lines → {table}.csv")

conn.close()