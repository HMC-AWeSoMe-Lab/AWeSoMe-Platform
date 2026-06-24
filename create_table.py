import sqlite3, os

db_path = os.path.expanduser("~/AWeSoMe-Platform/backend/database/database.db")

conn = sqlite3.connect(db_path)
conn.execute("""
CREATE TABLE IF NOT EXISTS questionnaire_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_id INTEGER,
    questionnaire TEXT NOT NULL,
    question_name TEXT NOT NULL,
    answer TEXT NOT NULL,
    current_timestamp DATETIME NOT NULL
)
""")
conn.commit()
conn.close()
print("Done — questionnaire_responses table created.")