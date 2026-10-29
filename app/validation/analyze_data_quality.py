import csv
import sqlite3
from collections import Counter
from pathlib import Path


# ==================================================
# CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]


def find_data_directory():
    """Choose the data directory containing both required files."""

    for folder_name in ("data_fresh", "data"):
        folder = BASE_DIR / folder_name
        database = folder / "customerpulse.db"
        ground_truth = folder / "ground_truth" / "ground_truth.csv"

        if database.exists() and ground_truth.exists():
            return folder

    raise FileNotFoundError(
        "Could not find a directory containing both required files:\n"
        "- customerpulse.db\n"
        "- ground_truth/ground_truth.csv\n"
        "Checked: data_fresh and data."
    )


DATA_DIR = find_data_directory()
DB_PATH = DATA_DIR / "customerpulse.db"
GROUND_TRUTH_PATH = DATA_DIR / "ground_truth" / "ground_truth.csv"

EXPECTED_SENTIMENTS = {"POSITIVE", "NEUTRAL", "NEGATIVE"}


# ==================================================
# MAIN ANALYSIS
# ==================================================

def main():

    print("=" * 65)
    print("CUSTOMERPULSE AI - DATA QUALITY ANALYSIS")
    print("=" * 65)

    print(f"\nDataset directory: {DATA_DIR}")
    print(f"Database: {DB_PATH}")
    print(f"Ground truth: {GROUND_TRUTH_PATH}")

    # Open database in read-only mode.
    connection = sqlite3.connect(
        f"{DB_PATH.resolve().as_uri()}?mode=ro",
        uri=True
    )
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        # --------------------------------------------------
        # 1. DATABASE RECORD COUNTS
        # --------------------------------------------------

        print("\n1. DATABASE RECORD COUNTS")

        expected_tables = [
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

        existing_tables = {
            row["name"]
            for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

        missing_tables = set(expected_tables) - existing_tables

        if missing_tables:
            raise RuntimeError(
                "Database is missing expected tables: "
                + ", ".join(sorted(missing_tables))
            )

        for table in expected_tables:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cursor.fetchone()[0]
            print(f"{table}: {count:,}")

        # --------------------------------------------------
        # 2. GROUND-TRUTH LABEL DISTRIBUTION
        # --------------------------------------------------

        print("\n2. GROUND-TRUTH LABEL DISTRIBUTION")

        sentiment_counts = Counter()
        theme_counts = Counter()

        total_rows = 0
        empty_sentiment = 0
        empty_theme = 0
        empty_interaction_id = 0
        invalid_sentiment = 0
        duplicate_interaction_ids = 0

        interaction_ids = set()

        required_columns = {
            "interaction_id",
            "true_sentiment",
            "true_theme",
        }

        with GROUND_TRUTH_PATH.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            actual_columns = set(reader.fieldnames or [])
            missing_columns = required_columns - actual_columns

            if missing_columns:
                raise ValueError(
                    "Ground-truth CSV is missing columns: "
                    + ", ".join(sorted(missing_columns))
                )

            for row in reader:
                total_rows += 1

                interaction_id = (
                    row.get("interaction_id") or ""
                ).strip()

                sentiment = (
                    row.get("true_sentiment") or ""
                ).strip().upper()

                theme = (
                    row.get("true_theme") or ""
                ).strip().upper()

                if not interaction_id:
                    empty_interaction_id += 1
                elif interaction_id in interaction_ids:
                    duplicate_interaction_ids += 1
                else:
                    interaction_ids.add(interaction_id)

                if not sentiment:
                    empty_sentiment += 1
                else:
                    sentiment_counts[sentiment] += 1

                    if sentiment not in EXPECTED_SENTIMENTS:
                        invalid_sentiment += 1

                if not theme:
                    empty_theme += 1
                else:
                    theme_counts[theme] += 1

        print(f"Total ground-truth rows: {total_rows:,}")

        print("\nSentiment distribution:")

        for label, count in sorted(sentiment_counts.items()):
            percentage = count / total_rows * 100 if total_rows else 0

            print(
                f"  {label}: {count:,} "
                f"({percentage:.2f}%)"
            )

        print("\nTheme distribution:")

        for theme, count in sorted(theme_counts.items()):
            percentage = count / total_rows * 100 if total_rows else 0

            print(
                f"  {theme}: {count:,} "
                f"({percentage:.2f}%)"
            )

        print(f"\nEmpty sentiment labels: {empty_sentiment}")
        print(f"Empty theme labels: {empty_theme}")
        print(f"Empty interaction IDs: {empty_interaction_id}")
        print(f"Invalid sentiment labels: {invalid_sentiment}")
        print(f"Duplicate interaction IDs: {duplicate_interaction_ids}")

        # --------------------------------------------------
        # 3. SAMPLE CUSTOMER FEEDBACK
        # --------------------------------------------------

        print("\n3. SAMPLE CUSTOMER FEEDBACK")

        sample_query = """
            SELECT
                i.interaction_id,
                CASE
                    WHEN i.review_id IS NOT NULL
                        THEN r.review_text
                    WHEN i.survey_response_id IS NOT NULL
                        THEN sr.response_text
                    WHEN i.support_message_id IS NOT NULL
                        THEN sm.message_text
                END AS feedback_text
            FROM interactions AS i
            LEFT JOIN reviews AS r
                ON i.review_id = r.review_id
            LEFT JOIN survey_responses AS sr
                ON i.survey_response_id = sr.response_id
            LEFT JOIN support_messages AS sm
                ON i.support_message_id = sm.message_id
            ORDER BY i.interaction_id
            LIMIT 15
        """

        for row in cursor.execute(sample_query):
            feedback = (
                row["feedback_text"] or "[EMPTY FEEDBACK]"
            )

            print(
                f"\nInteraction {row['interaction_id']}: "
                f"{feedback[:250]}"
            )

        # --------------------------------------------------
        # 4. EMPTY FEEDBACK CHECK
        # --------------------------------------------------

        print("\n4. EMPTY FEEDBACK CHECK")

        empty_feedback_query = """
            SELECT COUNT(*)
            FROM interactions AS i
            LEFT JOIN reviews AS r
                ON i.review_id = r.review_id
            LEFT JOIN survey_responses AS sr
                ON i.survey_response_id = sr.response_id
            LEFT JOIN support_messages AS sm
                ON i.support_message_id = sm.message_id
            WHERE TRIM(
                COALESCE(
                    r.review_text,
                    sr.response_text,
                    sm.message_text,
                    ''
                )
            ) = ''
        """

        cursor.execute(empty_feedback_query)
        empty_feedback = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM interactions")
        interaction_count = cursor.fetchone()[0]

        print(f"Total interactions: {interaction_count:,}")
        print(f"Empty feedback: {empty_feedback:,}")
        print(
            f"Non-empty feedback: "
            f"{interaction_count - empty_feedback:,}"
        )

        # --------------------------------------------------
        # 5. APPROVED THEME TAXONOMY
        # --------------------------------------------------

        print("\n5. APPROVED THEME TAXONOMY")

        cursor.execute(
            "SELECT theme_name FROM themes ORDER BY theme_name"
        )

        approved_themes = {
            row["theme_name"].strip().upper()
            for row in cursor.fetchall()
        }

        print(f"Approved themes: {len(approved_themes)}")

        for theme in sorted(approved_themes):
            print(f"  - {theme}")

        unknown_themes = set(theme_counts) - approved_themes

        if unknown_themes:
            print("\nWARNING: Ground truth contains unknown themes:")

            for theme in sorted(unknown_themes):
                print(f"  - {theme}")
        else:
            print("\nAll ground-truth themes match the taxonomy.")

        # --------------------------------------------------
        # 6. FOREIGN-KEY VALIDATION
        # --------------------------------------------------

        print("\n6. DATABASE INTEGRITY CHECKS")

        cursor.execute("PRAGMA foreign_key_check")
        foreign_key_errors = cursor.fetchall()

        print(f"Foreign-key violations: {len(foreign_key_errors)}")

        # Each interaction should reference exactly one source.
        cursor.execute("""
            SELECT COUNT(*)
            FROM interactions
            WHERE
                (CASE WHEN review_id IS NOT NULL THEN 1 ELSE 0 END)
              + (CASE WHEN survey_response_id IS NOT NULL THEN 1 ELSE 0 END)
              + (CASE WHEN support_message_id IS NOT NULL THEN 1 ELSE 0 END)
              != 1
        """)

        invalid_interactions = cursor.fetchone()[0]

        print(
            "Interactions with invalid source links: "
            f"{invalid_interactions}"
        )

        # --------------------------------------------------
        # 7. FINAL SUMMARY
        # --------------------------------------------------

        print("\n7. QUALITY SUMMARY")

        print(f"Ground-truth rows: {total_rows:,}")
        print(f"Database interactions: {interaction_count:,}")
        print(f"Empty feedback records: {empty_feedback:,}")
        print(f"Empty sentiment labels: {empty_sentiment:,}")
        print(f"Empty theme labels: {empty_theme:,}")
        print(f"Empty interaction IDs: {empty_interaction_id:,}")
        print(f"Invalid sentiment labels: {invalid_sentiment:,}")
        print(f"Duplicate interaction IDs: {duplicate_interaction_ids:,}")

        checks = {
            "Ground-truth row count matches interactions":
                total_rows == interaction_count,

            "All interactions contain feedback":
                empty_feedback == 0,

            "No empty sentiment labels":
                empty_sentiment == 0,

            "No empty theme labels":
                empty_theme == 0,

            "No empty interaction IDs":
                empty_interaction_id == 0,

            "No invalid sentiment labels":
                invalid_sentiment == 0,

            "No duplicate ground-truth interaction IDs":
                duplicate_interaction_ids == 0,

            "All themes belong to the approved taxonomy":
                not unknown_themes,

            "No foreign-key violations":
                len(foreign_key_errors) == 0,

            "Every interaction has exactly one source":
                invalid_interactions == 0,
        }

        for description, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            print(f"{status}: {description}")

        print("\n" + "=" * 65)

        if all(checks.values()):
            print("RESULT: ALL DATA QUALITY CHECKS PASSED")
        else:
            print("RESULT: SOME DATA QUALITY CHECKS FAILED")
            print("Review the warnings above before proceeding.")

        print("=" * 65)

    finally:
        connection.close()


if __name__ == "__main__":
    main()