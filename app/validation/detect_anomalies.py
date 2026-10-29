
import csv
import re
import sqlite3
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "customerpulse.db"
INPUT_FILE = BASE_DIR / "data" / "evaluation" / "anomaly_cases.csv"
OUTPUT_FILE = BASE_DIR / "data" / "evaluation" / "anomaly_report.csv"


def load_approved_themes():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT theme_name FROM themes WHERE is_active = 1"
        ).fetchall()

    return {row[0].strip().upper() for row in rows}


def detect_anomalies():
    with INPUT_FILE.open(
        "r", newline="", encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    approved_themes = load_approved_themes()

    # Count repeated text to find duplicate feedback.
    text_counts = Counter(
        row["model_input"].strip().casefold()
        for row in rows
        if row["model_input"].strip()
    )

    report = []

    for row in rows:
        text = row["model_input"]
        normalized_text = text.casefold()
        assigned_theme = row["assigned_theme"].strip().upper()

        findings = []

        # 1. Look for repeated feedback text.
        if text.strip() and text_counts[text.strip().casefold()] > 1:
            findings.append("DUPLICATE_RESPONSE")

        # 2. Look for email addresses in the feedback.
        if re.search(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            text,
            flags=re.IGNORECASE,
        ):
            findings.append("POTENTIAL_PII_LEAK")

        # 3. Check whether the theme belongs to the taxonomy.
        if assigned_theme not in approved_themes:
            findings.append("UNKNOWN_THEME")

        # 4. Check for obvious reference-label leakage.
        if re.search(
            r"\bTRUE_SENTIMENT\s*=",
            text,
            flags=re.IGNORECASE,
        ):
            findings.append("GROUND_TRUTH_LEAKAGE")

        # 5. Detect a simple, deliberately obvious contradiction.
        positive_words = (
            "excellent",
            "happy",
            "great",
            "love",
        )
        negative_words = (
            "terrible",
            "awful",
            "hate",
            "disappointed",
        )

        has_positive_word = any(
            word in normalized_text for word in positive_words
        )
        has_negative_word = any(
            word in normalized_text for word in negative_words
        )

        assigned_sentiment = row["assigned_sentiment"].upper()

        if (
            assigned_sentiment == "NEGATIVE"
            and has_positive_word
            and not has_negative_word
        ):
            findings.append("SENTIMENT_TEXT_CONTRADICTION")

        report.append({
            "case_id": row["case_id"],
            "interaction_id": row["interaction_id"],
            "expected_anomaly": row["anomaly_type"],
            "detected_anomalies": (
                ";".join(findings) if findings else "NONE"
            ),
            "expected_detection": row["expected_detection"],
            "expected_anomaly_detected": (
                "YES" if row["anomaly_type"] in findings else "NO"
            ),
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        fieldnames = [
            "case_id",
            "interaction_id",
            "expected_anomaly",
            "detected_anomalies",
            "expected_detection",
            "expected_anomaly_detected",
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report)

    successful = sum(
        item["expected_anomaly_detected"] == "YES"
        for item in report
    )

    print("CUSTOMERPULSE ANOMALY DETECTION")
    print("=" * 40)
    print(f"Cases checked: {len(report)}")
    print(f"Expected anomalies detected: {successful}/{len(report)}")
    print(f"Report saved to: {OUTPUT_FILE}")
    print("\nCase results:")

    for item in report:
        print(
            f'{item["case_id"]}: '
            f'{item["expected_anomaly_detected"]} — '
            f'{item["detected_anomalies"]}'
        )


if __name__ == "__main__":
    detect_anomalies()
