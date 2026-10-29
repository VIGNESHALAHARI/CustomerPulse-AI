
import csv
import sqlite3
from collections import Counter
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

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

VALID_SENTIMENTS = {
    "POSITIVE",
    "NEUTRAL",
    "NEGATIVE",
}

VALID_PRIORITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

VALID_ACTION_STATUSES = {
    "OPEN",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
}

VALID_SENDER_TYPES = {
    "CUSTOMER",
    "AGENT",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_check(description, passed, details=""):
    """Print a consistent PASS or FAIL message."""
    status = "PASS" if passed else "FAIL"
    suffix = f": {details}" if details else ""

    print(f"{status}: {description}{suffix}")

    return passed


def normalize_id(value):
    """Normalize IDs for reliable database and CSV comparisons."""
    if value is None:
        return ""

    return str(value).strip()


def get_table_names(connection):
    """Return all application table names."""
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()

    return {row[0] for row in rows}


def get_column_names(connection, table):
    """Return column names for a table."""
    rows = connection.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    return {row[1] for row in rows}


def validate_data():
    errors = []

    def check(description, passed, details=""):
        if not print_check(description, passed, details):
            errors.append(description)

    # --------------------------------------------------------
    # 1. Check required files
    # --------------------------------------------------------

    print("CUSTOMERPULSE AI - DATA VALIDATION")
    print("=" * 55)

    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}\n"
            "Run the database initialization and data generator first."
        )

    if not GROUND_TRUTH_PATH.exists():
        ground_truth_exists = False
        print_check(
            "Ground-truth file exists",
            False,
            str(GROUND_TRUTH_PATH),
        )
        errors.append("Ground-truth file exists")
    else:
        ground_truth_exists = True
        print_check("Ground-truth file exists", True)

    # --------------------------------------------------------
    # 2. Connect to database
    # --------------------------------------------------------

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        # Enable foreign-key enforcement on this connection.
        connection.execute("PRAGMA foreign_keys = ON")

        tables = get_table_names(connection)

        print("\n1. Required tables")

        required_tables = set(EXPECTED_COUNTS) | {
            "themes",
            "sentiment_labels",
            "interactions",
            "interaction_themes",
            "sentiment_predictions",
            "action_items",
        }

        for table in sorted(required_tables):
            check(
                f"Required table exists: {table}",
                table in tables,
            )

        # ----------------------------------------------------
        # 3. Record counts
        # ----------------------------------------------------

        print("\n2. Record counts")

        for table, expected in EXPECTED_COUNTS.items():
            if table not in tables:
                continue

            actual = connection.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]

            check(
                f"{table} record count",
                actual == expected,
                f"{actual:,} / {expected:,}",
            )

        # ----------------------------------------------------
        # 4. Required fields
        # ----------------------------------------------------

        print("\n3. Required-field checks")

        required_fields = {
            "customers": [
                "customer_name",
                "created_at",
            ],
            "products": [
                "product_name",
                "category",
                "created_at",
            ],
            "channels": [
                "channel_name",
            ],
            "surveys": [
                "survey_name",
                "start_date",
                "end_date",
            ],
            "survey_responses": [
                "customer_id",
                "product_id",
                "channel_id",
                "survey_id",
                "response_text",
                "response_date",
            ],
            "reviews": [
                "customer_id",
                "product_id",
                "channel_id",
                "rating",
                "review_text",
                "review_date",
            ],
            "support_messages": [
                "customer_id",
                "channel_id",
                "message_text",
                "message_date",
                "sender_type",
            ],
            "themes": [
                "theme_name",
                "is_active",
            ],
            "sentiment_labels": [
                "label_name",
            ],
        }

        for table, columns in required_fields.items():
            if table not in tables:
                continue

            existing_columns = get_column_names(
                connection,
                table,
            )

            for column in columns:
                if column not in existing_columns:
                    check(
                        f"{table}.{column} exists",
                        False,
                        "Column missing from schema",
                    )
                    continue

                missing_count = connection.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM "{table}"
                    WHERE "{column}" IS NULL
                       OR TRIM(CAST("{column}" AS TEXT)) = ''
                    """
                ).fetchone()[0]

                check(
                    f"{table}.{column} has no missing values",
                    missing_count == 0,
                    f"{missing_count:,} missing values",
                )

        # ----------------------------------------------------
        # 5. Primary-key checks
        # ----------------------------------------------------

        print("\n4. Primary-key checks")

        for table in sorted(tables):
            columns = connection.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()

            primary_keys = sorted(
                [
                    row
                    for row in columns
                    if row["pk"] > 0
                ],
                key=lambda row: row["pk"],
            )

            if not primary_keys:
                check(
                    f"{table} has a primary key",
                    False,
                    "No primary key declared",
                )
                continue

            pk_names = [
                row["name"]
                for row in primary_keys
            ]

            grouped_columns = ", ".join(
                f'"{name}"'
                for name in pk_names
            )

            null_condition = " OR ".join(
                f'"{name}" IS NULL'
                for name in pk_names
            )

            null_count = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM "{table}"
                WHERE {null_condition}
                """
            ).fetchone()[0]

            duplicate_count = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT {grouped_columns}
                    FROM "{table}"
                    GROUP BY {grouped_columns}
                    HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0]

            check(
                f"{table} primary key has no NULL values",
                null_count == 0,
                f"{null_count:,} affected rows",
            )

            check(
                f"{table} primary key is unique",
                duplicate_count == 0,
                f"{duplicate_count:,} duplicate groups",
            )

        # ----------------------------------------------------
        # 6. Foreign-key integrity
        # ----------------------------------------------------

        print("\n5. Foreign-key checks")

        foreign_key_violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        check(
            "Foreign-key integrity",
            len(foreign_key_violations) == 0,
            f"{len(foreign_key_violations):,} violations",
        )

        # ----------------------------------------------------
        # 7. Allowed values / enums
        # ----------------------------------------------------

        print("\n6. Allowed-value checks")

        enum_checks = [
            (
                "sentiment_labels",
                "label_name",
                VALID_SENTIMENTS,
            ),
            (
                "support_messages",
                "sender_type",
                VALID_SENDER_TYPES,
            ),
            (
                "action_items",
                "priority",
                VALID_PRIORITIES,
            ),
            (
                "action_items",
                "status",
                VALID_ACTION_STATUSES,
            ),
        ]

        for table, column, allowed_values in enum_checks:
            if table not in tables:
                continue

            columns = get_column_names(
                connection,
                table,
            )

            if column not in columns:
                check(
                    f"{table}.{column} exists",
                    False,
                    "Required enum column missing",
                )
                continue

            distinct_values = connection.execute(
                f'SELECT DISTINCT "{column}" FROM "{table}"'
            ).fetchall()

            invalid_values = [
                row[0]
                for row in distinct_values
                if row[0] not in allowed_values
            ]

            check(
                f"{table}.{column} contains allowed values",
                len(invalid_values) == 0,
                (
                    f"Invalid values: {invalid_values[:5]}"
                    if invalid_values
                    else "All values valid"
                ),
            )

        if "reviews" in tables:
            invalid_ratings = connection.execute(
                """
                SELECT COUNT(*)
                FROM reviews
                WHERE rating IS NULL
                   OR rating NOT BETWEEN 1 AND 5
                   OR rating != CAST(rating AS INTEGER)
                """
            ).fetchone()[0]

            check(
                "Review ratings are integers from 1 to 5",
                invalid_ratings == 0,
                f"{invalid_ratings:,} invalid ratings",
            )

        # ----------------------------------------------------
        # 8. Date validity
        # ----------------------------------------------------

        print("\n7. Date-validity checks")

        date_checks = [
            ("customers", "created_at"),
            ("products", "created_at"),
            ("surveys", "start_date"),
            ("surveys", "end_date"),
            ("reviews", "review_date"),
            ("survey_responses", "response_date"),
            ("support_messages", "message_date"),
            ("interactions", "interaction_date"),
        ]

        for table, column in date_checks:
            if table not in tables:
                continue

            columns = get_column_names(
                connection,
                table,
            )

            if column not in columns:
                check(
                    f"{table}.{column} exists",
                    False,
                    "Date column missing",
                )
                continue

            invalid_dates = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM "{table}"
                WHERE "{column}" IS NULL
                   OR date("{column}") IS NULL
                   OR date("{column}") != substr("{column}", 1, 10)
                """
            ).fetchone()[0]

            check(
                f"{table}.{column} contains valid ISO dates",
                invalid_dates == 0,
                f"{invalid_dates:,} invalid or missing dates",
            )

        # ----------------------------------------------------
        # 9. Survey lifecycle
        # ----------------------------------------------------

        print("\n8. Survey lifecycle checks")

        if "surveys" in tables:
            invalid_survey_periods = connection.execute(
                """
                SELECT COUNT(*)
                FROM surveys
                WHERE date(start_date) IS NULL
                   OR date(end_date) IS NULL
                   OR date(start_date) > date(end_date)
                """
            ).fetchone()[0]

            check(
                "Survey start date is not after end date",
                invalid_survey_periods == 0,
                f"{invalid_survey_periods:,} invalid periods",
            )

        if {
            "survey_responses",
            "surveys",
        }.issubset(tables):
            invalid_response_dates = connection.execute(
                """
                SELECT COUNT(*)
                FROM survey_responses AS r
                JOIN surveys AS s
                  ON s.survey_id = r.survey_id
                WHERE date(r.response_date) IS NULL
                   OR date(r.response_date) < date(s.start_date)
                   OR date(r.response_date) > date(s.end_date)
                """
            ).fetchone()[0]

            check(
                "Survey responses fall within their survey periods",
                invalid_response_dates == 0,
                f"{invalid_response_dates:,} outside survey period",
            )

        # ----------------------------------------------------
        # 10. Interaction relationships
        # ----------------------------------------------------

        print("\n9. Interaction checks")

        if "interactions" in tables:
            source_columns = [
                "survey_response_id",
                "review_id",
                "support_message_id",
            ]

            interaction_columns = get_column_names(
                connection,
                "interactions",
            )

            if all(
                column in interaction_columns
                for column in source_columns
            ):
                invalid_interactions = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM interactions
                    WHERE
                        (survey_response_id IS NOT NULL) +
                        (review_id IS NOT NULL) +
                        (support_message_id IS NOT NULL) != 1
                    """
                ).fetchone()[0]

                check(
                    "Each interaction has exactly one source",
                    invalid_interactions == 0,
                    f"{invalid_interactions:,} invalid interactions",
                )

                source_tables = [
                    "survey_responses",
                    "reviews",
                    "support_messages",
                ]

                expected_interactions = sum(
                    connection.execute(
                        f'SELECT COUNT(*) FROM "{table}"'
                    ).fetchone()[0]
                    for table in source_tables
                    if table in tables
                )

                actual_interactions = connection.execute(
                    "SELECT COUNT(*) FROM interactions"
                ).fetchone()[0]

                check(
                    "Source records reconcile with interactions",
                    actual_interactions == expected_interactions,
                    (
                        f"{actual_interactions:,} interactions / "
                        f"{expected_interactions:,} source records"
                    ),
                )

                source_mappings = [
                    (
                        "survey_response_id",
                        "survey_responses",
                        "response_id",
                    ),
                    (
                        "review_id",
                        "reviews",
                        "review_id",
                    ),
                    (
                        "support_message_id",
                        "support_messages",
                        "message_id",
                    ),
                ]

                for source_column, source_table, source_id in source_mappings:
                    if source_table not in tables:
                        continue

                    duplicate_sources = connection.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM (
                            SELECT "{source_column}"
                            FROM interactions
                            WHERE "{source_column}" IS NOT NULL
                            GROUP BY "{source_column}"
                            HAVING COUNT(*) > 1
                        )
                        """
                    ).fetchone()[0]

                    missing_sources = connection.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM "{source_table}" AS s
                        LEFT JOIN interactions AS i
                          ON i."{source_column}" = s."{source_id}"
                        WHERE i.interaction_id IS NULL
                        """
                    ).fetchone()[0]

                    check(
                        f"{source_table} maps to at most one interaction",
                        duplicate_sources == 0,
                        f"{duplicate_sources:,} duplicate mappings",
                    )

                    check(
                        f"Every {source_table} record has an interaction",
                        missing_sources == 0,
                        f"{missing_sources:,} missing mappings",
                    )

        # ----------------------------------------------------
        # 11. Exact duplicate source records
        # ----------------------------------------------------

        print("\n10. Duplicate source-record checks")

        duplicate_queries = {
            "reviews": """
                SELECT COUNT(*)
                FROM (
                    SELECT customer_id, product_id, channel_id,
                           rating, review_text, review_date
                    FROM reviews
                    GROUP BY customer_id, product_id, channel_id,
                             rating, review_text, review_date
                    HAVING COUNT(*) > 1
                )
            """,
            "survey_responses": """
                SELECT COUNT(*)
                FROM (
                    SELECT customer_id, product_id, channel_id,
                           survey_id, response_text, response_date
                    FROM survey_responses
                    GROUP BY customer_id, product_id, channel_id,
                             survey_id, response_text, response_date
                    HAVING COUNT(*) > 1
                )
            """,
            "support_messages": """
                SELECT COUNT(*)
                FROM (
                    SELECT customer_id, product_id, channel_id,
                           conversation_id, message_text,
                           message_date, sender_type
                    FROM support_messages
                    GROUP BY customer_id, product_id, channel_id,
                             conversation_id, message_text,
                             message_date, sender_type
                    HAVING COUNT(*) > 1
                )
            """,
        }

        for table, query in duplicate_queries.items():
            if table not in tables:
                continue

            duplicates = connection.execute(query).fetchone()[0]

            check(
                f"{table} has no exact duplicate records",
                duplicates == 0,
                f"{duplicates:,} duplicate groups",
            )

        # ----------------------------------------------------
        # 12. Theme taxonomy
        # ----------------------------------------------------

        print("\n11. Theme taxonomy checks")

        approved_themes = set()

        if "themes" in tables:
            approved_themes = {
                str(row[0]).strip().upper()
                for row in connection.execute(
                    """
                    SELECT theme_name
                    FROM themes
                    WHERE is_active = 1
                    """
                )
            }

            check(
                "Exactly 10 active themes are configured",
                len(approved_themes) == 10,
                f"{len(approved_themes)} active themes",
            )

            duplicate_theme_names = connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT UPPER(TRIM(theme_name))
                    FROM themes
                    GROUP BY UPPER(TRIM(theme_name))
                    HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0]

            check(
                "Theme names are unique",
                duplicate_theme_names == 0,
                f"{duplicate_theme_names:,} duplicate theme groups",
            )

        if "interaction_themes" in tables:
            invalid_interaction_themes = connection.execute(
                """
                SELECT COUNT(*)
                FROM interaction_themes AS it
                LEFT JOIN themes AS t
                  ON t.theme_id = it.theme_id
                WHERE t.theme_id IS NULL
                   OR t.is_active != 1
                   OR it.confidence IS NULL
                   OR it.confidence < 0
                   OR it.confidence > 1
                """
            ).fetchone()[0]

            check(
                "Interaction themes use active taxonomy and valid confidence",
                invalid_interaction_themes == 0,
                f"{invalid_interaction_themes:,} invalid records",
            )

        # ----------------------------------------------------
        # 13. Sentiment predictions
        # ----------------------------------------------------

        print("\n12. Sentiment prediction checks")

        if "sentiment_predictions" in tables:
            prediction_columns = get_column_names(
                connection,
                "sentiment_predictions",
            )

            required_prediction_columns = {
                "interaction_id",
                "sentiment_label_id",
                "confidence",
                "model_version",
                "predicted_at",
            }

            missing_prediction_columns = (
                required_prediction_columns - prediction_columns
            )

            check(
                "Prediction schema has required columns",
                not missing_prediction_columns,
                (
                    f"Missing: {sorted(missing_prediction_columns)}"
                    if missing_prediction_columns
                    else "All required columns exist"
                ),
            )

            if not missing_prediction_columns:
                invalid_predictions = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM sentiment_predictions AS sp
                    LEFT JOIN interactions AS i
                      ON i.interaction_id = sp.interaction_id
                    LEFT JOIN sentiment_labels AS sl
                      ON sl.sentiment_label_id = sp.sentiment_label_id
                    WHERE i.interaction_id IS NULL
                       OR sl.sentiment_label_id IS NULL
                       OR sl.label_name NOT IN (
                           'POSITIVE', 'NEUTRAL', 'NEGATIVE'
                       )
                       OR sp.confidence IS NULL
                       OR sp.confidence < 0
                       OR sp.confidence > 1
                       OR sp.model_version IS NULL
                       OR TRIM(sp.model_version) = ''
                       OR date(sp.predicted_at) IS NULL
                    """
                ).fetchone()[0]

                check(
                    "Predictions have valid labels, confidence, and metadata",
                    invalid_predictions == 0,
                    f"{invalid_predictions:,} invalid predictions",
                )

        # ----------------------------------------------------
        # 14. Action-item checks
        # ----------------------------------------------------

        print("\n13. Action-item checks")

        if "action_items" in tables:
            invalid_actions = connection.execute(
                """
                SELECT COUNT(*)
                FROM action_items AS a
                LEFT JOIN themes AS t
                  ON t.theme_id = a.theme_id
                WHERE t.theme_id IS NULL
                   OR t.is_active != 1
                   OR a.title IS NULL
                   OR TRIM(a.title) = ''
                   OR a.description IS NULL
                   OR TRIM(a.description) = ''
                   OR a.priority NOT IN (
                       'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
                   )
                   OR a.status NOT IN (
                       'OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
                   )
                """
            ).fetchone()[0]

            check(
                "Action items have valid themes and fields",
                invalid_actions == 0,
                f"{invalid_actions:,} invalid action items",
            )

        # ----------------------------------------------------
        # 15. Ground-truth integrity
        # ----------------------------------------------------

        print("\n14. Ground-truth checks")

        if ground_truth_exists:
            with GROUND_TRUTH_PATH.open(
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                reader = csv.DictReader(file)
                ground_truth_rows = list(reader)
                ground_truth_columns = set(reader.fieldnames or [])

            required_gt_columns = {
                "interaction_id",
                "true_sentiment",
                "true_theme",
            }

            missing_gt_columns = (
                required_gt_columns - ground_truth_columns
            )

            check(
                "Ground-truth required columns exist",
                not missing_gt_columns,
                (
                    f"Missing columns: {sorted(missing_gt_columns)}"
                    if missing_gt_columns
                    else f"Columns: {sorted(ground_truth_columns)}"
                ),
            )

            check(
                "Ground-truth row count is 70,000",
                len(ground_truth_rows) == EXPECTED_COUNTS["interactions"],
                f"{len(ground_truth_rows):,} rows",
            )

            gt_ids = [
                normalize_id(row.get("interaction_id"))
                for row in ground_truth_rows
            ]

            nonempty_gt_ids = [
                interaction_id
                for interaction_id in gt_ids
                if interaction_id
            ]

            gt_id_counts = Counter(nonempty_gt_ids)

            duplicate_gt_ids = sum(
                1
                for count in gt_id_counts.values()
                if count > 1
            )

            check(
                "Ground-truth interaction IDs are unique",
                duplicate_gt_ids == 0,
                f"{duplicate_gt_ids:,} duplicate ID groups",
            )

            empty_gt_ids = sum(
                1
                for interaction_id in gt_ids
                if not interaction_id
            )

            check(
                "Ground-truth interaction IDs are not empty",
                empty_gt_ids == 0,
                f"{empty_gt_ids:,} empty IDs",
            )

            if not missing_gt_columns:
                invalid_gt_sentiments = [
                    row.get("true_sentiment", "").strip()
                    for row in ground_truth_rows
                    if row.get("true_sentiment", "").strip()
                    not in VALID_SENTIMENTS
                ]

                check(
                    "Ground-truth sentiment labels are valid",
                    len(invalid_gt_sentiments) == 0,
                    f"{len(invalid_gt_sentiments):,} invalid labels",
                )

                invalid_gt_themes = [
                    row.get("true_theme", "").strip()
                    for row in ground_truth_rows
                    if row.get("true_theme", "").strip().upper()
                    not in approved_themes
                ]

                check(
                    "Ground-truth themes belong to taxonomy",
                    len(invalid_gt_themes) == 0,
                    f"{len(invalid_gt_themes):,} invalid themes",
                )

                database_ids = {
                    normalize_id(row[0])
                    for row in connection.execute(
                        "SELECT interaction_id FROM interactions"
                    )
                }

                ground_truth_ids = set(nonempty_gt_ids)

                missing_ids = database_ids - ground_truth_ids
                unknown_ids = ground_truth_ids - database_ids

                check(
                    "Every interaction has ground truth",
                    len(missing_ids) == 0,
                    f"{len(missing_ids):,} missing IDs",
                )

                check(
                    "Ground truth contains no unknown interactions",
                    len(unknown_ids) == 0,
                    f"{len(unknown_ids):,} unknown IDs",
                )

                check(
                    "Ground-truth ID count matches database interaction count",
                    len(ground_truth_ids) == len(database_ids),
                    (
                        f"{len(ground_truth_ids):,} ground-truth IDs / "
                        f"{len(database_ids):,} database IDs"
                    ),
                )

    # --------------------------------------------------------
    # 16. Final result
    # --------------------------------------------------------

    print("\n" + "=" * 55)

    if errors:
        print(f"VALIDATION FAILED: {len(errors)} issue(s) found")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print("VALIDATION PASSED: All checks passed successfully.")


if __name__ == "__main__":
    validate_data()
