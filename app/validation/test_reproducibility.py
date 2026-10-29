
import hashlib
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
GENERATOR = BASE_DIR / "app" / "data_generation" / "generate_data.py"

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
]



def database_checksum(database_path):
    """Calculate a stable checksum and always close the connection."""
    digest = hashlib.sha256()
    connection = sqlite3.connect(database_path)

    try:
        for table in TABLES:
            digest.update(table.encode("utf-8"))

            cursor = connection.execute(
                f'SELECT * FROM "{table}" ORDER BY 1'
            )

            for row in cursor:
                digest.update(repr(row).encode("utf-8"))
                digest.update(b"\n")

    finally:
        connection.close()

    return digest.hexdigest()



def generate_in_temporary_directory(directory):
    """Generate a fresh dataset in an isolated directory."""
    directory.mkdir(parents=True, exist_ok=True)

    output_directory = directory / "data"

    environment = os.environ.copy()
    environment["CUSTOMERPULSE_SEED"] = "20261022"
    environment["CUSTOMERPULSE_OUTPUT_DIR"] = str(output_directory)

    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=BASE_DIR,
        env=environment,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Data generation failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    database_path = output_directory / "customerpulse.db"

    if not database_path.exists():
        raise FileNotFoundError(
            f"Generated database not found: {database_path}"
        )

    return database_checksum(database_path)


def main():
    if not GENERATOR.exists():
        raise FileNotFoundError(
            f"Generator file not found: {GENERATOR}"
        )

    with tempfile.TemporaryDirectory(
        prefix="customerpulse_test_"
    ) as temporary_root:
        root = Path(temporary_root)

        print("Generating the first dataset...")
        first_checksum = generate_in_temporary_directory(
            root / "run_one"
        )

        print("Generating the second dataset...")
        second_checksum = generate_in_temporary_directory(
            root / "run_two"
        )

    print("\nCUSTOMERPULSE REPRODUCIBILITY TEST")
    print("=" * 45)
    print("Seed: 20261022")
    print(f"Run 1 checksum: {first_checksum}")
    print(f"Run 2 checksum: {second_checksum}")

    if first_checksum == second_checksum:
        print("\nPASS: Both generated datasets match.")
    else:
        print("\nFAIL: The generated datasets differ.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
