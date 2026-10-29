
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "customerpulse.db"
OUTPUT_DIR = BASE_DIR / "data" / "evaluation"
OUTPUT_FILE = OUTPUT_DIR / "anomaly_cases.csv"


def get_sample_interactions():
    """Read a few real records from our synthetic database."""

    query = """
        SELECT
            i.interaction_id,
            sr.response_text,
            r.review_text,
            sm.message_text
        FROM interactions i
        LEFT JOIN survey_responses sr
            ON i.survey_response_id = sr.response_id
        LEFT JOIN reviews r
            ON i.review_id = r.review_id
        LEFT JOIN support_messages sm
            ON i.support_message_id = sm.message_id
        ORDER BY i.interaction_id
        LIMIT 10
    """

    with sqlite3.connect(DB_PATH) as connection:
        return connection.execute(query).fetchall()


def create_anomaly_cases():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    records = get_sample_interactions()

    if len(records) < 2:
        raise ValueError(
            "At least two interactions are required."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pick existing synthetic records for reference.
    first = records[0]
    second = records[1]

    first_text = (
        first[1] or first[2] or first[3] or ""
    )
    second_text = (
        second[1] or second[2] or second[3] or ""
    )

    cases = [
        {
            "case_id": "ANOMALY_001",
            "interaction_id": first[0],
            "model_input": (
                "The delivery was excellent and arrived "
                "on time. I am very happy with the service."
            ),
            "assigned_sentiment": "NEGATIVE",
            "assigned_theme": "DELIVERY",
            "anomaly_type": "SENTIMENT_TEXT_CONTRADICTION",
            "expected_detection": "Sentiment conflicts with clearly positive text.",
        },
        {
            "case_id": "ANOMALY_002",
            "interaction_id": second[0],
            "model_input": second_text,
            "assigned_sentiment": "NEUTRAL",
            "assigned_theme": "PRODUCT_QUALITY",
            "anomaly_type": "DUPLICATE_RESPONSE",
            "expected_detection": "This row is duplicated in the evaluation dataset.",
        },
        {
            "case_id": "ANOMALY_002_DUP",
            "interaction_id": second[0],
            "model_input": second_text,
            "assigned_sentiment": "NEUTRAL",
            "assigned_theme": "PRODUCT_QUALITY",
            "anomaly_type": "DUPLICATE_RESPONSE",
            "expected_detection": "Duplicate of ANOMALY_002.",
        },
        {
            "case_id": "ANOMALY_003",
            "interaction_id": first[0],
            "model_input": (
                "Please contact me at "
                "customer.private@example.com about my order."
            ),
            "assigned_sentiment": "NEUTRAL",
            "assigned_theme": "CUSTOMER_SUPPORT",
            "anomaly_type": "POTENTIAL_PII_LEAK",
            "expected_detection": "An email address appears in the message text.",
        },
        {
            "case_id": "ANOMALY_004",
            "interaction_id": second[0],
            "model_input": second_text,
            "assigned_sentiment": "NEUTRAL",
            "assigned_theme": "UNAPPROVED_THEME_XYZ",
            "anomaly_type": "UNKNOWN_THEME",
            "expected_detection": "Theme is not part of the approved taxonomy.",
        },
        {
            "case_id": "ANOMALY_005",
            "interaction_id": first[0],
            "model_input": (
                "Customer feedback text. "
                "TRUE_SENTIMENT=POSITIVE"
            ),
            "assigned_sentiment": "POSITIVE",
            "assigned_theme": "PRODUCT_QUALITY",
            "anomaly_type": "GROUND_TRUTH_LEAKAGE",
            "expected_detection": "Reference label has leaked into model input.",
        },
    ]

    columns = [
        "case_id",
        "interaction_id",
        "model_input",
        "assigned_sentiment",
        "assigned_theme",
        "anomaly_type",
        "expected_detection",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
        )
        writer.writeheader()
        writer.writerows(cases)

    print("Anomaly evaluation dataset created!")
    print(f"Cases written: {len(cases)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("Original database records were not modified.")


if __name__ == "__main__":
    create_anomaly_cases()
