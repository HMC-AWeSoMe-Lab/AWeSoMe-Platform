import sqlite3
import os 

# ********WARNING: RUNNING THIS CLEARS DATABASE.DB*********
# If you do clear the database, make sure to "INSERT INTO latest_id (interaction_id) VALUES (0);"

# This makes it work no matter where you run the script from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def initialize_database():
    """
    Initialize the database by running the schema and inserting default values.
    WARNING: This will clear all existing data!
    """
    schema_path = os.path.join(BASE_DIR, 'schema.sql')
    
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'))
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())

    # Initialize the latest_id table with a default value
    conn.execute("INSERT INTO latest_id (interaction_id) VALUES (0);")

    conn.commit()
    conn.close()

# Only run the initialization if this script is executed directly
if __name__ == '__main__':
    print("⚠️  WARNING: This will CLEAR the database and reinitialize all tables!")
    print("All existing data will be permanently lost.")
    
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        initialize_database()
        print("Database initialized successfully!")
    else:
        print("Database initialization cancelled.")
