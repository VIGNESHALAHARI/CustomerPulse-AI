
import csv
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "customerpulse.db"
EXPORT_DIR = BASE_DIR / "data" / "generated"

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


def export_table(connection, table_name):
    cursor = connection.execute(
        f'SELECT * FROM "{table_name}" ORDER BY 1'
    )

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    # Export CSV
    csv_path = EXPORT_DIR / f"{table_name}.csv"

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    # Export JSON
    json_path = EXPORT_DIR / f"{table_name}.json"

    records = [
        dict(zip(columns, row))
        for row in rows
    ]

    with json_path.open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    print(
        f"{table_name}: {len(rows):,} records exported"
    )


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        for table_name in TABLES:
            export_table(connection, table_name)

    print("\nExport completed successfully!")
    print(f"Export directory: {EXPORT_DIR}")


if __name__ == "__main__":
    main()
