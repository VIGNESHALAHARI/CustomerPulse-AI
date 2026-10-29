import csv
import re
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


# ==================================================
# DATABASE HELPERS
# ==================================================

def get_feedback(connection):
    """Retrieve feedback text for every standardized interaction."""

    query = """
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
    """

    return connection.execute(query).fetchall()


def load_ground_truth():
    """Load ground-truth labels separately from model input data."""

    required_columns = {
        "interaction_id",
        "true_sentiment",
        "true_theme",
    }

    ground_truth_by_id = {}

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
            interaction_id = (
                row.get("interaction_id") or ""
            ).strip()

            if not interaction_id:
                continue

            if interaction_id in ground_truth_by_id:
                raise ValueError(
                    "Duplicate interaction ID in ground truth: "
                    f"{interaction_id}"
                )

            ground_truth_by_id[interaction_id] = {
                "sentiment": (
                    row.get("true_sentiment") or ""
                ).strip().upper(),

                "theme": (
                    row.get("true_theme") or ""
                ).strip().upper(),
            }

    return ground_truth_by_id


# ==================================================
# TEXT QUALITY ANALYSIS
# ==================================================

def main():

    print("=" * 65)
    print("CUSTOMERPULSE AI - TEXT QUALITY ANALYSIS")
    print("=" * 65)

    print(f"\nDataset directory: {DATA_DIR}")
    print(f"Database: {DB_PATH}")
    print(f"Ground truth: {GROUND_TRUTH_PATH}")

    # Open the database in read-only mode.
    connection = sqlite3.connect(
        f"{DB_PATH.resolve().as_uri()}?mode=ro",
        uri=True
    )
    connection.row_factory = sqlite3.Row

    try:
        # --------------------------------------------------
        # 1. LOAD FEEDBACK AND LABELS
        # --------------------------------------------------

        feedback_rows = get_feedback(connection)
        ground_truth_by_id = load_ground_truth()

        feedback_by_id = {}

        for row in feedback_rows:
            interaction_id = str(row["interaction_id"]).strip()
            feedback = (row["feedback_text"] or "").strip()

            feedback_by_id[interaction_id] = feedback

        total_records = len(feedback_by_id)

        # --------------------------------------------------
        # 2. FEEDBACK DIVERSITY
        # --------------------------------------------------

        print("\n1. FEEDBACK DIVERSITY")

        feedback_counts = Counter(feedback_by_id.values())

        unique_feedback = len(feedback_counts)
        duplicate_records = total_records - unique_feedback

        unique_percentage = (
            unique_feedback / total_records * 100
            if total_records else 0
        )

        print(f"Total feedback records: {total_records:,}")
        print(f"Unique feedback messages: {unique_feedback:,}")
        print(f"Repeated feedback records: {duplicate_records:,}")
        print(
            f"Unique-message percentage: "
            f"{unique_percentage:.2f}%"
        )

        empty_feedback = sum(
            1 for text in feedback_by_id.values() if not text
        )

        print(f"Empty feedback messages: {empty_feedback:,}")

        # --------------------------------------------------
        # 3. MOST FREQUENT FEEDBACK
        # --------------------------------------------------

        print("\n2. MOST FREQUENT FEEDBACK")

        repeated_messages = [
            (text, count)
            for text, count in feedback_counts.most_common(10)
            if count > 1
        ]

        if repeated_messages:
            for text, count in repeated_messages:
                preview = text[:160] if text else "[EMPTY FEEDBACK]"

                print(f"\nOccurrences: {count}")
                print(f"Text: {preview}")
        else:
            print("No repeated feedback messages were found.")

        # --------------------------------------------------
        # 4. POSSIBLE EMAIL ADDRESS CHECK
        # --------------------------------------------------

        print("\n3. POSSIBLE EMAIL ADDRESS CHECK")

        email_pattern = re.compile(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            flags=re.IGNORECASE
        )

        possible_email_count = 0
        email_examples = []

        for interaction_id, feedback in feedback_by_id.items():
            if email_pattern.search(feedback):
                possible_email_count += 1

                if len(email_examples) < 5:
                    email_examples.append(interaction_id)

        print(
            "Feedback records containing possible email addresses: "
            f"{possible_email_count:,}"
        )

        if email_examples:
            print(
                "Example interaction IDs to review: "
                + ", ".join(email_examples)
            )

        print(
            "Note: This is a simple email-pattern check, "
            "not a complete PII detector."
        )

        # --------------------------------------------------
        # 5. GROUND-TRUTH COVERAGE
        # --------------------------------------------------

        print("\n4. GROUND-TRUTH COVERAGE")

        feedback_ids = set(feedback_by_id)
        ground_truth_ids = set(ground_truth_by_id)

        missing_labels = feedback_ids - ground_truth_ids
        unknown_interactions = ground_truth_ids - feedback_ids

        print(f"Feedback records: {len(feedback_ids):,}")
        print(f"Ground-truth records: {len(ground_truth_ids):,}")
        print(f"Feedback without ground-truth labels: {len(missing_labels):,}")
        print(
            "Ground-truth IDs without matching feedback: "
            f"{len(unknown_interactions):,}"
        )

        # --------------------------------------------------
        # 6. SAMPLE FEEDBACK WITH LABELS
        # --------------------------------------------------

        print("\n5. SAMPLE FEEDBACK WITH GROUND-TRUTH LABELS")

        shown = 0

        for interaction_id in sorted(feedback_ids):
            if interaction_id not in ground_truth_by_id:
                continue

            feedback = feedback_by_id[interaction_id]
            labels = ground_truth_by_id[interaction_id]

            print(f"\nInteraction ID: {interaction_id}")
            print(f"Feedback: {feedback[:300] or '[EMPTY FEEDBACK]'}")
            print(f"Sentiment: {labels['sentiment']}")
            print(f"Theme: {labels['theme']}")

            shown += 1

            if shown >= 20:
                break

        if shown == 0:
            print("No matching feedback and ground-truth records were found.")

        # --------------------------------------------------
        # 7. LABEL DISTRIBUTION
        # --------------------------------------------------

        print("\n6. LABEL DISTRIBUTION")

        sentiment_counts = Counter()
        theme_counts = Counter()

        for labels in ground_truth_by_id.values():
            if labels["sentiment"]:
                sentiment_counts[labels["sentiment"]] += 1

            if labels["theme"]:
                theme_counts[labels["theme"]] += 1

        print("\nSentiment:")

        for label, count in sorted(sentiment_counts.items()):
            print(f"  {label}: {count:,}")

        print("\nThemes:")

        for theme, count in sorted(theme_counts.items()):
            print(f"  {theme}: {count:,}")

        # --------------------------------------------------
        # 8. FINAL SUMMARY
        # --------------------------------------------------

        print("\n7. TEXT QUALITY SUMMARY")

        checks = {
            "Feedback records have unique interaction IDs":
                len(feedback_by_id) == len(feedback_rows),

            "No empty feedback records":
                empty_feedback == 0,

            "All feedback has a ground-truth label":
                len(missing_labels) == 0,

            "No ground-truth IDs are missing from the database":
                len(unknown_interactions) == 0,

            "No possible email addresses found":
                possible_email_count == 0,
        }

        for description, passed in checks.items():
            print(
                f'{"PASS" if passed else "WARNING"}: {description}'
            )

        print("\n" + "=" * 65)
        print("TEXT QUALITY ANALYSIS COMPLETED")
        print("=" * 65)

    finally:
        connection.close()


if __name__ == "__main__":
    main()