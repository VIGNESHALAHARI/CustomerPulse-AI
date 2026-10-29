import sqlite3
from pathlib import Path

# Find the project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Define database and schema paths
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "customerpulse.db"
SCHEMA_PATH = BASE_DIR / "app" / "database" / "schema.sql"


def initialize_database():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}"
        )

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)

        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

    print("Database initialized successfully!")
    print(f"Database location: {DB_PATH}")
    print(f"Tables created: {len(tables)}")

    for (table_name,) in tables:
        print(f"  - {table_name}")


if __name__ == "__main__":
    initialize_database()