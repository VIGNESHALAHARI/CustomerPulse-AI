import json
import sqlite3
from pathlib import Path

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data_fresh"
DB_PATH = DATA_DIR / "customerpulse.db"
GROUND_TRUTH_PATH = DATA_DIR / "ground_truth" / "ground_truth.csv"

MODEL_DIR = ROOT_DIR / "models"
REPORT_DIR = ROOT_DIR / "reports"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# LOAD FEEDBACK FROM SQLITE
# --------------------------------------------------

def load_dataset():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground-truth CSV not found: {GROUND_TRUTH_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            i.interaction_id,
            i.interaction_date,
            COALESCE(sr.response_text, r.review_text, sm.message_text)
                AS feedback_text,
            COALESCE(sr.product_id, r.product_id, sm.product_id)
                AS product_id,
            COALESCE(sr.channel_id, r.channel_id, sm.channel_id)
                AS channel_id
        FROM interactions AS i
        LEFT JOIN survey_responses AS sr
            ON i.survey_response_id = sr.response_id
        LEFT JOIN reviews AS r
            ON i.review_id = r.review_id
        LEFT JOIN support_messages AS sm
            ON i.support_message_id = sm.message_id
        ORDER BY i.interaction_id
    """

    try:
        feedback = pd.read_sql_query(query, connection)
    finally:
        connection.close()

    labels = pd.read_csv(GROUND_TRUTH_PATH)

    required_columns = {
        "interaction_id",
        "true_sentiment",
        "true_theme",
    }

    missing = required_columns - set(labels.columns)

    if missing:
        raise ValueError(
            f"Ground-truth CSV is missing columns: {sorted(missing)}"
        )

    # Ground truth is used only as target labels.
    # It is never included in the text features.
    dataset = feedback.merge(
        labels[
            ["interaction_id", "true_sentiment", "true_theme"]
        ],
        on="interaction_id",
        how="inner",
        validate="one_to_one",
    )

    dataset = dataset.dropna(
        subset=["feedback_text", "true_sentiment", "true_theme"]
    )

    dataset["feedback_text"] = (
        dataset["feedback_text"].astype(str).str.strip()
    )

    dataset = dataset[dataset["feedback_text"] != ""]

    if dataset.empty:
        raise ValueError("No usable feedback records were loaded.")

    if dataset["interaction_id"].duplicated().any():
        raise ValueError("Duplicate interaction IDs found.")

    if len(dataset) != len(feedback):
        print(
            "WARNING: Some feedback rows did not have usable ground-truth "
            "labels or text."
        )

    return dataset


# --------------------------------------------------
# TRAIN/TEST SPLIT
# Group identical feedback texts together so exact
# duplicates cannot appear in both train and test.
# --------------------------------------------------

def split_dataset(dataset):
    groups = dataset["feedback_text"].str.lower().str.strip()

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=20261022,
    )

    train_indices, test_indices = next(
        splitter.split(dataset, groups=groups)
    )

    train = dataset.iloc[train_indices].copy()
    test = dataset.iloc[test_indices].copy()

    if set(groups.iloc[train_indices]).intersection(
        set(groups.iloc[test_indices])
    ):
        raise RuntimeError(
            "Identical feedback text was found in both train and test."
        )

    return train, test


# --------------------------------------------------
# TRAIN AND EVALUATE ONE CLASSIFIER
# --------------------------------------------------

def train_classifier(train, test, target_column, model_name):
    model = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    max_features=30000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=20261022,
                ),
            ),
        ]
    )

    model.fit(
        train["feedback_text"],
        train[target_column],
    )

    predictions = model.predict(test["feedback_text"])

    labels = sorted(
        set(test[target_column]) | set(predictions)
    )

    report = classification_report(
        test[target_column],
        predictions,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        test[target_column],
        predictions,
        labels=labels,
    )

    metrics = {
        "model": model_name,
        "training_rows": int(len(train)),
        "test_rows": int(len(test)),
        "accuracy": float(
            accuracy_score(test[target_column], predictions)
        ),
        "macro_f1": float(
            f1_score(
                test[target_column],
                predictions,
                average="macro",
                zero_division=0,
            )
        ),
        "classification_report": report,
        "confusion_matrix": {
            "labels": labels,
            "matrix": matrix.tolist(),
        },
    }

    output_path = MODEL_DIR / f"{model_name}_model.joblib"
    joblib.dump(model, output_path)

    print(f"\n{'=' * 60}")
    print(f"{model_name.upper()} MODEL")
    print("=" * 60)
    print(f"Training rows: {len(train):,}")
    print(f"Testing rows:  {len(test):,}")
    print(f"Accuracy:      {metrics['accuracy']:.4f}")
    print(f"Macro F1:      {metrics['macro_f1']:.4f}")
    print("\nClassification report:")
    print(
        classification_report(
            test[target_column],
            predictions,
            labels=labels,
            zero_division=0,
        )
    )
    print("Confusion matrix:")
    print(matrix)
    print(f"Saved model: {output_path}")

    return metrics


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    print("=" * 60)
    print("CUSTOMERPULSE AI - MODEL TRAINING")
    print("=" * 60)

    print(f"Database: {DB_PATH}")
    print(f"Ground truth: {GROUND_TRUTH_PATH}")

    dataset = load_dataset()

    print(f"\nUsable feedback records: {len(dataset):,}")
    print("\nSentiment label counts:")
    print(dataset["true_sentiment"].value_counts())

    print("\nTheme label counts:")
    print(dataset["true_theme"].value_counts())

    train, test = split_dataset(dataset)

    print(f"\nTraining records: {len(train):,}")
    print(f"Testing records:  {len(test):,}")
    print(
        "Exact text overlap between train and test: "
        f"{len(set(train['feedback_text'].str.lower().str.strip()) & set(test['feedback_text'].str.lower().str.strip()))}"
    )

    sentiment_metrics = train_classifier(
        train,
        test,
        target_column="true_sentiment",
        model_name="sentiment",
    )

    theme_metrics = train_classifier(
        train,
        test,
        target_column="true_theme",
        model_name="theme",
    )

    results = {
        "dataset_rows": int(len(dataset)),
        "random_seed": 20261022,
        "split_method": "GroupShuffleSplit grouped by normalized exact feedback text",
        "note": (
            "Synthetic-data evaluation. Exact duplicate feedback texts "
            "are kept in one split. Results may not represent performance "
            "on real customer feedback."
        ),
        "sentiment": sentiment_metrics,
        "theme": theme_metrics,
    }

    report_path = REPORT_DIR / "model_evaluation.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    print("\n" + "=" * 60)
    print("MODEL TRAINING COMPLETED")
    print("=" * 60)
    print(f"Evaluation report: {report_path}")
    print(f"Saved models in:   {MODEL_DIR}")


if __name__ == "__main__":
    main()