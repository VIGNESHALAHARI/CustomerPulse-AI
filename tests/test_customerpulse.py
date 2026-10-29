import csv
import sqlite3
from pathlib import Path

import pytest


# ============================================================
# PROJECT PATHS AND EXPECTED COUNTS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data_fresh"
DB_PATH = OUTPUT_DIR / "customerpulse.db"
GROUND_TRUTH_PATH = (
    OUTPUT_DIR / "ground_truth" / "ground_truth.csv"
)

EXPECTED_COUNTS = {
    "customers": 5000,
    "products": 20,
    "channels": 5,
    "surveys": 8,
    "themes": 10,
    "sentiment_labels": 3,
    "reviews": 25000,
    "survey_responses": 25000,
    "support_messages": 20000,
    "interactions": 70000,
}

VALID_SENTIMENTS = {
    "POSITIVE",
    "NEUTRAL",
    "NEGATIVE",
}


# ============================================================
# DATABASE FIXTURE
# ============================================================

@pytest.fixture(scope="module")
def connection():
    """
    Open the existing database in read-only mode.

    These tests inspect existing data without modifying it.
    """
    if not DB_PATH.is_file():
        pytest.skip(f"Database not found: {DB_PATH}")

    database_uri = DB_PATH.resolve().as_uri() + "?mode=ro"

    conn = sqlite3.connect(database_uri, uri=True)

    try:
        yield conn
    finally:
        conn.close()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def table_count(conn, table_name):
    """Return the number of records in an approved table."""

    allowed_tables = set(EXPECTED_COUNTS)

    if table_name not in allowed_tables:
        raise ValueError(
            f"Unexpected table name: {table_name}"
        )

    query = f"SELECT COUNT(*) FROM {table_name}"

    return conn.execute(query).fetchone()[0]


def read_ground_truth():
    """
    Read the ground-truth CSV.

    Returns the column names and all CSV rows.
    """
    if not GROUND_TRUTH_PATH.is_file():
        pytest.skip(
            f"Ground-truth CSV not found: {GROUND_TRUTH_PATH}"
        )

    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            pytest.fail("Ground-truth CSV has no header.")

        fieldnames = reader.fieldnames
        rows = list(reader)

    return fieldnames, rows


# ============================================================
# TEST 1: DATABASE TABLE COUNTS
# ============================================================

def test_expected_reference_data_counts(connection):
    """Verify expected master/reference record counts."""

    expected = {
        "customers": 5000,
        "products": 20,
        "channels": 5,
        "surveys": 8,
        "themes": 10,
        "sentiment_labels": 3,
    }

    for table, expected_count in expected.items():
        actual_count = table_count(connection, table)

        assert actual_count == expected_count, (
            f"{table}: expected {expected_count}, "
            f"found {actual_count}"
        )


# ============================================================
# TEST 2: EVENT COUNTS
# ============================================================

def test_expected_event_counts(connection):
    """Verify reviews, survey responses, messages, and interactions."""

    expected = {
        "reviews": 25000,
        "survey_responses": 25000,
        "support_messages": 20000,
        "interactions": 70000,
    }

    for table, expected_count in expected.items():
        actual_count = table_count(connection, table)

        assert actual_count == expected_count, (
            f"{table}: expected {expected_count}, "
            f"found {actual_count}"
        )


# ============================================================
# TEST 3: EXACTLY ONE SOURCE PER INTERACTION
# ============================================================

def test_interactions_have_exactly_one_source(connection):
    """
    Each interaction must reference exactly one source:
    review, survey response, or support message.
    """

    invalid_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM interactions
        WHERE
            (
                CASE WHEN review_id IS NOT NULL
                     THEN 1 ELSE 0 END
                +
                CASE WHEN survey_response_id IS NOT NULL
                     THEN 1 ELSE 0 END
                +
                CASE WHEN support_message_id IS NOT NULL
                     THEN 1 ELSE 0 END
            ) != 1
        """
    ).fetchone()[0]

    assert invalid_count == 0, (
        f"Found {invalid_count} interactions "
        "with an invalid number of source links."
    )


# ============================================================
# TEST 4: FOREIGN-KEY INTEGRITY
# ============================================================

def test_foreign_keys_are_valid(connection):
    """Check for foreign-key violations throughout the database."""

    violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    assert not violations, (
        f"Foreign-key violations found: {violations[:10]}"
    )


# ============================================================
# TEST 5: VALID REVIEW RATINGS
# ============================================================

def test_review_ratings_are_valid(connection):
    """Every review rating must be an integer from 1 to 5."""

    invalid_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM reviews
        WHERE rating IS NULL
           OR rating < 1
           OR rating > 5
           OR rating != CAST(rating AS INTEGER)
        """
    ).fetchone()[0]

    assert invalid_count == 0, (
        f"Found {invalid_count} invalid review ratings."
    )


# ============================================================
# TEST 6: UNIQUE SOURCE EVENT IDS
# ============================================================

def test_source_event_ids_are_not_duplicated(connection):
    """Verify that source event IDs are unique."""

    checks = {
        "reviews": "review_id",
        "survey_responses": "response_id",
        "support_messages": "message_id",
    }

    for table, column in checks.items():
        duplicate_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT {column}
                FROM {table}
                GROUP BY {column}
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        assert duplicate_count == 0, (
            f"Duplicate IDs found in {table}.{column}"
        )


# ============================================================
# TEST 7: UNIQUE INTERACTION IDS
# ============================================================

def test_interaction_ids_are_not_duplicated(connection):
    """Verify that interaction IDs are unique."""

    duplicate_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT interaction_id
            FROM interactions
            GROUP BY interaction_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    assert duplicate_count == 0, (
        f"Found {duplicate_count} duplicated interaction IDs."
    )


# ============================================================
# TEST 8: GROUND-TRUTH FILE EXISTS
# ============================================================

def test_ground_truth_file_exists():
    """Verify that the ground-truth CSV exists."""

    assert GROUND_TRUTH_PATH.is_file(), (
        f"Ground-truth file not found: {GROUND_TRUTH_PATH}"
    )


# ============================================================
# TEST 9: GROUND-TRUTH ROW COUNT
# ============================================================

def test_ground_truth_has_expected_row_count():
    """Ground truth must contain exactly 70,000 data rows."""

    _, rows = read_ground_truth()

    assert len(rows) == 70000, (
        f"Expected 70000 ground-truth rows, "
        f"found {len(rows)}"
    )


# ============================================================
# TEST 10: VALID GROUND-TRUTH SENTIMENT LABELS
# ============================================================

def test_ground_truth_sentiment_labels_are_valid():
    """
    Validate the true_sentiment column.

    The actual generated CSV uses:
    interaction_id, true_sentiment, true_theme
    """

    fieldnames, rows = read_ground_truth()

    label_column = "true_sentiment"

    assert label_column in fieldnames, (
        f"Missing '{label_column}' column. "
        f"Available columns: {fieldnames}"
    )

    invalid_labels = set()

    for row in rows:
        label = (
            row.get(label_column) or ""
        ).strip().upper()

        if label not in VALID_SENTIMENTS:
            invalid_labels.add(label)

    assert not invalid_labels, (
        f"Invalid sentiment labels: {sorted(invalid_labels)}"
    )


# ============================================================
# TEST 11: GROUND-TRUTH THEME LABELS ARE PRESENT
# ============================================================

def test_ground_truth_theme_labels_are_present():
    """Verify that every ground-truth row has a theme label."""

    fieldnames, rows = read_ground_truth()

    assert "true_theme" in fieldnames, (
        "Missing 'true_theme' column. "
        f"Available columns: {fieldnames}"
    )

    empty_theme_rows = [
        index
        for index, row in enumerate(rows, start=2)
        if not (row.get("true_theme") or "").strip()
    ]

    assert not empty_theme_rows, (
        "Empty theme labels found on CSV lines: "
        f"{empty_theme_rows[:10]}"
    )


# ============================================================
# TEST 12: GROUND-TRUTH INTERACTION IDS
# ============================================================

def test_ground_truth_interaction_ids_are_unique_and_valid(connection):
    """
    Verify that each ground-truth interaction ID is unique
    and corresponds to a database interaction.
    """

    fieldnames, rows = read_ground_truth()

    assert "interaction_id" in fieldnames, (
        "Missing 'interaction_id' column in ground truth."
    )

    csv_ids = []

    for line_number, row in enumerate(rows, start=2):
        raw_id = (row.get("interaction_id") or "").strip()

        assert raw_id, (
            f"Missing interaction_id on CSV line {line_number}."
        )

        try:
            interaction_id = int(raw_id)
        except ValueError:
            pytest.fail(
                f"Invalid interaction_id '{raw_id}' "
                f"on CSV line {line_number}."
            )

        csv_ids.append(interaction_id)

    assert len(csv_ids) == len(set(csv_ids)), (
        "Duplicate interaction IDs found in ground truth."
    )

    database_ids = {
        row[0]
        for row in connection.execute(
            "SELECT interaction_id FROM interactions"
        )
    }

    csv_id_set = set(csv_ids)

    missing_from_database = csv_id_set - database_ids
    missing_from_ground_truth = database_ids - csv_id_set

    assert not missing_from_database, (
        "Ground-truth IDs missing from the database: "
        f"{sorted(missing_from_database)[:10]}"
    )

    assert not missing_from_ground_truth, (
        "Database interaction IDs missing from ground truth: "
        f"{sorted(missing_from_ground_truth)[:10]}"
    )