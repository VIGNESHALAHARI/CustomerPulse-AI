import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "customerpulse.db"
GROUND_TRUTH_PATH = (
    BASE_DIR / "data" / "ground_truth" / "ground_truth.csv"
)

EXPECTED_COUNTS = {
    "customers": 5000,
    "products": 20,
    "channels": 5,
    "surveys": 8,
    "reviews": 25000,
    "survey_responses": 25000,
    "support_messages": 20000,
    "interactions": 70000,
}


def validate_data():
    errors = []

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        print("CUSTOMERPULSE DATA VALIDATION")
        print("=" * 40)

        # 1. Validate record counts
        print("\n1. Record counts")

        for table, expected in EXPECTED_COUNTS.items():
            actual = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            status = "PASS" if actual == expected else "FAIL"
            print(
                f"{status}: {table}: "
                f"{actual:,} / {expected:,}"
            )

            if actual != expected:
                errors.append(
                    f"{table}: expected {expected}, found {actual}"
                )

        # 2. Validate required fields
        print("\n2. Required-field checks")

        checks = {
            "customers": [
                "customer_name",
                "created_at",
            ],
            "products": [
                "product_name",
                "category",
                "created_at",
            ],
            "reviews": [
                "review_text",
                "review_date",
            ],
            "survey_responses": [
                "response_text",
                "response_date",
            ],
            "support_messages": [
                "message_text",
                "message_date",
            ],
        }

        for table, columns in checks.items():
            for column in columns:
                query = (
                    f'SELECT COUNT(*) FROM "{table}" '
                    f'WHERE "{column}" IS NULL '
                    f'OR TRIM(CAST("{column}" AS TEXT)) = \'\''
                )

                count = connection.execute(query).fetchone()[0]

                status = "PASS" if count == 0 else "FAIL"
                print(
                    f"{status}: {table}.{column}: "
                    f"{count} missing"
                )

                if count:
                    errors.append(
                        f"{table}.{column}: {count} missing values"
                    )

        # 3. Validate foreign keys
        print("\n3. Foreign-key checks")

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if violations:
            print(f"FAIL: {len(violations)} foreign-key violations")
            errors.append(
                f"{len(violations)} foreign-key violations"
            )
        else:
            print("PASS: No foreign-key violations")

        # 4. Validate interaction source uniqueness
        print("\n4. Interaction checks")

        invalid_interactions = connection.execute("""
            SELECT COUNT(*)
            FROM interactions
            WHERE
                (
                    (survey_response_id IS NOT NULL)
                    + (review_id IS NOT NULL)
                    + (support_message_id IS NOT NULL)
                ) != 1
        """).fetchone()[0]

        if invalid_interactions:
            print(
                f"FAIL: {invalid_interactions} invalid interactions"
            )
            errors.append("Invalid interaction source assignments")
        else:
            print("PASS: Every interaction has exactly one source")

        # 5. Validate ground truth
        print("\n5. Ground-truth checks")

        if not GROUND_TRUTH_PATH.exists():
            errors.append("Ground-truth CSV is missing")
            print("FAIL: Ground-truth CSV is missing")
        else:
            with GROUND_TRUTH_PATH.open(
                "r",
                newline="",
                encoding="utf-8",
            ) as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            expected_columns = {
                "interaction_id",
                "true_sentiment",
                "true_theme",
            }

            if not expected_columns.issubset(reader.fieldnames or []):
                errors.append("Ground-truth columns are incorrect")
                print("FAIL: Ground-truth columns are incorrect")
            else:
                print(f"Ground-truth records: {len(rows):,}")

                if len(rows) != 70000:
                    errors.append(
                        f"Expected 70000 ground-truth rows, "
                        f"found {len(rows)}"
                    )
                    print("FAIL: Incorrect ground-truth row count")
                else:
                    print("PASS: Ground-truth row count")

                valid_sentiments = {
                    "POSITIVE",
                    "NEUTRAL",
                    "NEGATIVE",
                }

                invalid_labels = sum(
                    row["true_sentiment"] not in valid_sentiments
                    for row in rows
                )

                if invalid_labels:
                    errors.append(
                        f"{invalid_labels} invalid sentiment labels"
                    )
                    print(
                        f"FAIL: {invalid_labels} invalid sentiment labels"
                    )
                else:
                    print("PASS: Sentiment labels are valid")

    # 6. Final result
    print("\n" + "=" * 40)

    if errors:
        print(f"VALIDATION FAILED: {len(errors)} issue(s) found")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print("VALIDATION PASSED: All current checks succeeded!")


if __name__ == "__main__":
    validate_data()