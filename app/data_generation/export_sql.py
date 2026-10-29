
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "customerpulse.db"
OUTPUT_FILE = BASE_DIR / "data" / "generated" / "customerpulse_seed.sql"

TABLES = [
    "customers",
    "products",
    "channels",
    "surveys",
    "survey_responses",
    "reviews",
    "support_messages",
    "interactions",
    "themes",
    "sentiment_labels",
    "interaction_themes",
    "sentiment_predictions",
    "action_items",
]


def sql_value(value):
    """Convert a Python value into a SQL literal."""

    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (int, float)):
        return str(value)

    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def export_sql():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        with OUTPUT_FILE.open("w", encoding="utf-8") as file:
            file.write("-- CustomerPulse SQL seed data\n")
            file.write("-- Generated from the current SQLite database.\n\n")
            file.write("PRAGMA foreign_keys = ON;\n\n")
            file.write("BEGIN TRANSACTION;\n\n")

            # Insert parent tables before dependent tables.
            for table in TABLES:
                cursor = connection.execute(
                    f'SELECT * FROM "{table}" ORDER BY 1'
                )

                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

                for row in rows:
                    column_sql = ", ".join(
                        f'"{column}"' for column in columns
                    )
                    values_sql = ", ".join(
                        sql_value(value) for value in row
                    )

                    file.write(
                        f'INSERT INTO "{table}" '
                        f"({column_sql}) VALUES ({values_sql});\n"
                    )

                file.write("\n")

            file.write("COMMIT;\n")

    print("SQL seed export completed!")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    export_sql()
