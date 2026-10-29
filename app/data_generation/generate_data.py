import csv
import os
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


# ==================================================
# CONFIGURATION
# ==================================================

SEED = int(os.environ.get("CUSTOMERPULSE_SEED", "20261022"))

TOTAL_CUSTOMERS = 5_000
TOTAL_REVIEWS = 25_000
TOTAL_SURVEY_RESPONSES = 25_000
TOTAL_SUPPORT_MESSAGES = 20_000

TOTAL_INTERACTIONS = (
    TOTAL_REVIEWS
    + TOTAL_SURVEY_RESPONSES
    + TOTAL_SUPPORT_MESSAGES
)

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = Path(
    os.environ.get(
        "CUSTOMERPULSE_OUTPUT_DIR",
        str(BASE_DIR / "data"),
    )
).resolve()

DB_PATH = OUTPUT_DIR / "customerpulse.db"

GROUND_TRUTH_DIR = OUTPUT_DIR / "ground_truth"
GROUND_TRUTH_PATH = GROUND_TRUTH_DIR / "ground_truth.csv"

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2026, 10, 1)

random.seed(SEED)


# ==================================================
# PRODUCTS
# ==================================================

PRODUCTS = [
    ("Smartphone", "Electronics"),
    ("Laptop", "Electronics"),
    ("Headphones", "Electronics"),
    ("Smartwatch", "Electronics"),
    ("Coffee Maker", "Home Appliances"),
    ("Air Purifier", "Home Appliances"),
    ("Office Chair", "Furniture"),
    ("Desk Lamp", "Furniture"),
    ("Running Shoes", "Fashion"),
    ("Backpack", "Fashion"),
    ("Water Bottle", "Lifestyle"),
    ("Fitness Tracker", "Electronics"),
    ("Keyboard", "Electronics"),
    ("Wireless Mouse", "Electronics"),
    ("Monitor", "Electronics"),
    ("Tablet", "Electronics"),
    ("Blender", "Home Appliances"),
    ("Travel Mug", "Lifestyle"),
    ("Jacket", "Fashion"),
    ("Desk", "Furniture"),
]

CHANNELS = [
    "WEBSITE",
    "MOBILE_APP",
    "EMAIL",
    "RETAIL_STORE",
    "SOCIAL_MEDIA",
]

REGIONS = [
    "North",
    "South",
    "East",
    "West",
    "Central",
]


# ==================================================
# THEMES AND SENTIMENTS
# ==================================================

THEMES = [
    ("PRODUCT_QUALITY", "Durability and product quality"),
    ("DELIVERY", "Delivery speed and reliability"),
    ("CUSTOMER_SUPPORT", "Customer service experience"),
    ("PRICING", "Price, discounts, and value"),
    ("USABILITY", "Ease of use"),
    ("PAYMENT", "Payment experience"),
    ("RETURNS", "Returns and refunds"),
    ("AVAILABILITY", "Product availability"),
    ("PACKAGING", "Packaging quality"),
    ("FEATURES", "Product features and functionality"),
]

SENTIMENTS = [
    "POSITIVE",
    "NEUTRAL",
    "NEGATIVE",
]


# ==================================================
# FEEDBACK TEMPLATES
# ==================================================

FEEDBACK_TEMPLATES = {
    "PRODUCT_QUALITY": {
        "POSITIVE": [
            "The {product} feels durable and well made.",
            "The build quality of this {product} is excellent.",
            "My {product} works reliably after regular use.",
            "I am impressed with the materials used in this {product}.",
            "The {product} performs consistently and feels premium.",
            "The quality of this {product} exceeded my expectations.",
        ],
        "NEUTRAL": [
            "The {product} has acceptable build quality.",
            "The materials used in this {product} meet expectations.",
            "My {product} works as described so far.",
            "The {product} has average durability.",
            "The build quality is neither impressive nor disappointing.",
            "The {product} performs adequately for normal use.",
        ],
        "NEGATIVE": [
            "The {product} stopped working after a few days.",
            "The build quality of this {product} is disappointing.",
            "My {product} feels fragile and poorly assembled.",
            "The materials used in this {product} seem cheap.",
            "I noticed defects in my {product} shortly after purchase.",
            "The {product} does not feel durable enough.",
        ],
    },
    "DELIVERY": {
        "POSITIVE": [
            "My {product} arrived earlier than expected.",
            "The delivery was quick and the package arrived safely.",
            "My order arrived on time without problems.",
            "The delivery updates were accurate and helpful.",
            "I received my {product} sooner than promised.",
            "The courier delivered my order promptly.",
        ],
        "NEUTRAL": [
            "My {product} arrived within the estimated delivery window.",
            "The delivery took approximately the expected amount of time.",
            "My order arrived on the scheduled date.",
            "The delivery experience was fairly ordinary.",
            "The package arrived without major delivery issues.",
            "The delivery time matched the original estimate.",
        ],
        "NEGATIVE": [
            "My {product} arrived several days late.",
            "The delivery was delayed without a useful explanation.",
            "I received no clear updates about my delayed order.",
            "My package took longer to arrive than promised.",
            "The courier repeatedly postponed the delivery.",
            "I am disappointed by the delay in receiving my {product}.",
        ],
    },
    "CUSTOMER_SUPPORT": {
        "POSITIVE": [
            "The support agent resolved my issue quickly.",
            "Customer service was helpful and professional.",
            "The support team explained the solution clearly.",
            "I received a helpful response from customer support.",
            "The agent listened carefully and solved my problem.",
            "Customer service followed up and resolved my concern.",
        ],
        "NEUTRAL": [
            "Customer support answered my question adequately.",
            "The support agent provided the basic information I needed.",
            "My support request received a standard response.",
            "The customer service experience was average.",
            "The agent explained the usual troubleshooting steps.",
            "Customer support responded within the stated timeframe.",
        ],
        "NEGATIVE": [
            "Customer support did not resolve my issue.",
            "The support agent was unhelpful and dismissive.",
            "I contacted customer service several times without a solution.",
            "The support team gave me confusing instructions.",
            "My support request remained unresolved.",
            "Customer service took too long to address my problem.",
        ],
    },
    "PRICING": {
        "POSITIVE": [
            "The price of this {product} offers excellent value.",
            "I received great value for the amount I paid.",
            "The discount made this {product} affordable.",
            "This {product} is reasonably priced for its quality.",
            "The price was competitive with similar products.",
            "I am satisfied with the value for money.",
        ],
        "NEUTRAL": [
            "The price of this {product} seems reasonable.",
            "The cost is similar to other products in this category.",
            "The price was close to what I expected.",
            "The product offers average value for its cost.",
            "The discount was modest but acceptable.",
            "The price did not significantly affect my decision.",
        ],
        "NEGATIVE": [
            "This {product} is too expensive for its quality.",
            "The price was higher than I expected.",
            "I found a similar product at a much lower price.",
            "The discount was smaller than advertised.",
            "This product does not offer enough value for the money.",
            "I am disappointed with the high cost of this {product}.",
        ],
    },
    "USABILITY": {
        "POSITIVE": [
            "The {product} is easy to use and understand.",
            "The controls on this {product} are intuitive.",
            "I learned how to use the {product} very quickly.",
            "The interface is simple and easy to navigate.",
            "Using this {product} feels straightforward.",
            "The setup process was simple and convenient.",
        ],
        "NEUTRAL": [
            "The {product} is reasonably easy to operate.",
            "The controls work as expected.",
            "The interface is usable but fairly ordinary.",
            "It took a little time to understand the controls.",
            "The setup instructions were adequate.",
            "The navigation is acceptable for everyday use.",
        ],
        "NEGATIVE": [
            "The {product} is confusing to operate.",
            "The controls are difficult to understand.",
            "I struggled to complete the initial setup.",
            "The interface is complicated and frustrating.",
            "Using the {product} requires too many unnecessary steps.",
            "The instructions did not explain how to operate the product.",
        ],
    },
    "PAYMENT": {
        "POSITIVE": [
            "The payment was processed quickly and securely.",
            "Checkout accepted my payment without any issues.",
            "The payment confirmation arrived immediately.",
            "Paying for my order was simple and convenient.",
            "The transaction completed successfully on the first attempt.",
            "The payment process was smooth and reliable.",
        ],
        "NEUTRAL": [
            "The payment was processed within the expected timeframe.",
            "Checkout worked as expected.",
            "The payment confirmation arrived after a short delay.",
            "The transaction completed without major issues.",
            "The payment process was fairly standard.",
            "The available payment options met my basic needs.",
        ],
        "NEGATIVE": [
            "My payment was charged twice for one order.",
            "The payment failed several times during checkout.",
            "I was charged but did not receive an order confirmation.",
            "The checkout page displayed an unexpected payment error.",
            "My transaction remained pending for too long.",
            "The payment process was confusing and frustrating.",
        ],
    },
    "RETURNS": {
        "POSITIVE": [
            "Returning my {product} was simple and hassle-free.",
            "The refund arrived quickly after I returned the product.",
            "The return instructions were clear and helpful.",
            "Customer service processed my refund promptly.",
            "The return pickup was arranged without problems.",
            "I received the correct refund without unnecessary delays.",
        ],
        "NEUTRAL": [
            "The return process followed the stated procedure.",
            "My refund was processed within the expected timeframe.",
            "The return instructions were reasonably clear.",
            "The refund process was acceptable overall.",
            "I returned the product using the standard procedure.",
            "The return request was handled as expected.",
        ],
        "NEGATIVE": [
            "My refund has been delayed for several weeks.",
            "The return process was unnecessarily complicated.",
            "I returned the product but have not received my refund.",
            "The return request was rejected without a clear explanation.",
            "I had difficulty arranging a return pickup.",
            "The refund amount was less than I expected.",
        ],
    },
    "AVAILABILITY": {
        "POSITIVE": [
            "The {product} was available when I needed it.",
            "I easily found the {product} in stock.",
            "My preferred product was available for immediate purchase.",
            "The store had plenty of stock available.",
            "I was able to order the {product} without waiting.",
            "The product availability information was accurate.",
        ],
        "NEUTRAL": [
            "The {product} was available at the time of purchase.",
            "Stock availability was consistent with the listing.",
            "The product was available in the standard selection.",
            "The availability information was adequate.",
            "The item was in stock when I checked.",
            "The product selection met my basic requirements.",
        ],
        "NEGATIVE": [
            "The {product} was out of stock when I tried to buy it.",
            "The listing showed availability but the item was unavailable.",
            "I had to wait several weeks for the product to return to stock.",
            "My preferred product was unavailable in the required size.",
            "The store frequently runs out of this product.",
            "I could not purchase the {product} because it was unavailable.",
        ],
    },
    "PACKAGING": {
        "POSITIVE": [
            "My {product} arrived in secure and undamaged packaging.",
            "The packaging protected the product very well.",
            "The package was neat and professionally presented.",
            "The protective materials kept my product safe.",
            "The packaging was easy to open and recycle.",
            "My order arrived neatly packed and in excellent condition.",
        ],
        "NEUTRAL": [
            "The packaging was adequate for the product.",
            "My {product} arrived in standard packaging.",
            "The package provided sufficient basic protection.",
            "The packaging was ordinary but functional.",
            "The box had no major damage.",
            "The packaging met basic expectations.",
        ],
        "NEGATIVE": [
            "The package arrived with damaged protective materials.",
            "My {product} was poorly packed inside the box.",
            "The packaging was torn when the order arrived.",
            "The box provided insufficient protection for the product.",
            "The package arrived crushed and damaged.",
            "There was excessive and unnecessary packaging material.",
        ],
    },
    "FEATURES": {
        "POSITIVE": [
            "The features of this {product} are useful and reliable.",
            "The {product} includes all the features I needed.",
            "The new features make this product more convenient.",
            "The functionality of the {product} exceeded my expectations.",
            "The available features work as intended.",
            "I am impressed by the useful features of this product.",
        ],
        "NEUTRAL": [
            "The {product} includes the expected basic features.",
            "The available features meet my minimum requirements.",
            "The functionality is adequate for everyday tasks.",
            "The product features are similar to competing models.",
            "The feature set is acceptable but not exceptional.",
            "The product performs its advertised basic functions.",
        ],
        "NEGATIVE": [
            "The {product} is missing features I expected.",
            "Several advertised features do not work properly.",
            "The product lacks important functionality.",
            "The available features are less useful than expected.",
            "Some essential features are difficult to access.",
            "The product does not provide the functionality I need.",
        ],
    },
}


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def random_date():
    """Generate a reproducible timestamp within the configured range."""
    seconds = int((END_DATE - START_DATE).total_seconds())

    generated = START_DATE + timedelta(
        seconds=random.randint(0, seconds)
    )

    return generated.isoformat(timespec="seconds")


def random_sentiment():
    """Choose a synthetic sentiment using fixed probabilities."""
    return random.choices(
        SENTIMENTS,
        weights=[0.45, 0.20, 0.35],
        k=1,
    )[0]


def choose_theme():
    """Choose a theme from the approved theme taxonomy."""
    return random.choice(THEMES)[0]


def generate_feedback(theme, sentiment, product):
    """Generate synthetic feedback aligned with theme and sentiment."""
    template = random.choice(
        FEEDBACK_TEMPLATES[theme][sentiment]
    )

    return template.format(product=product)


def get_connection():
    """Connect to SQLite and initialize the database schema if needed."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    schema_path = BASE_DIR / "app" / "database" / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(
            f"Could not find database schema: {schema_path}"
        )

    if not DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as schema_connection:
            schema_connection.executescript(
                schema_path.read_text(encoding="utf-8")
            )

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def get_id_map(cursor, table, id_column, name_column):
    """Map a reference table's names to IDs."""
    rows = cursor.execute(
        f"SELECT {id_column}, {name_column} FROM {table}"
    ).fetchall()

    return {name: record_id for record_id, name in rows}


# ==================================================
# GENERATE REFERENCE DATA
# ==================================================

def generate_reference_data(connection):
    cursor = connection.cursor()

    cursor.executemany(
        """
        INSERT OR IGNORE INTO channels (channel_name)
        VALUES (?)
        """,
        [(channel,) for channel in CHANNELS],
    )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO themes
            (theme_name, description, is_active)
        VALUES (?, ?, 1)
        """,
        THEMES,
    )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO sentiment_labels (label_name)
        VALUES (?)
        """,
        [(sentiment,) for sentiment in SENTIMENTS],
    )

    existing_products = cursor.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if existing_products == 0:
        cursor.executemany(
            """
            INSERT INTO products
                (product_name, category, created_at)
            VALUES (?, ?, ?)
            """,
            [
                (name, category, "2025-01-01T00:00:00")
                for name, category in PRODUCTS
            ],
        )

    existing_customers = cursor.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    if existing_customers == 0:
        customer_rows = []

        for customer_id in range(1, TOTAL_CUSTOMERS + 1):
            customer_rows.append(
                (
                    customer_id,
                    f"Synthetic Customer {customer_id}",
                    f"customer{customer_id}@example.com",
                    random.choice(REGIONS),
                    random_date(),
                )
            )

        cursor.executemany(
            """
            INSERT INTO customers
                (customer_id, customer_name, email, region, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            customer_rows,
        )

    existing_surveys = cursor.execute(
        "SELECT COUNT(*) FROM surveys"
    ).fetchone()[0]

    if existing_surveys == 0:
        survey_rows = []

        for survey_id in range(1, 9):
            survey_rows.append(
                (
                    survey_id,
                    f"Customer Experience Survey {survey_id}",
                    "2025-01-01",
                    "2026-12-31",
                )
            )

        cursor.executemany(
            """
            INSERT INTO surveys
                (survey_id, survey_name, start_date, end_date)
            VALUES (?, ?, ?, ?)
            """,
            survey_rows,
        )

    connection.commit()


# ==================================================
# LOAD REFERENCE IDS
# ==================================================

def load_reference_ids(connection):
    cursor = connection.cursor()

    customers = [
        row[0]
        for row in cursor.execute(
            "SELECT customer_id FROM customers ORDER BY customer_id"
        ).fetchall()
    ]

    products = cursor.execute(
        """
        SELECT product_id, product_name
        FROM products
        ORDER BY product_id
        """
    ).fetchall()

    channels = [
        row[0]
        for row in cursor.execute(
            "SELECT channel_id FROM channels ORDER BY channel_id"
        ).fetchall()
    ]

    surveys = [
        row[0]
        for row in cursor.execute(
            "SELECT survey_id FROM surveys ORDER BY survey_id"
        ).fetchall()
    ]

    return customers, products, channels, surveys


# ==================================================
# EXPORT GROUND TRUTH
# ==================================================

def export_ground_truth(rows):
    """Export labels separately from the feedback text."""
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        GROUND_TRUTH_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            ["interaction_id", "true_sentiment", "true_theme"]
        )

        writer.writerows(
            sorted(rows, key=lambda row: row[0])
        )

    print(f"Ground truth exported to: {GROUND_TRUTH_PATH}")


# ==================================================
# GENERATE REVIEWS
# ==================================================

def generate_reviews(
    connection,
    customers,
    products,
    channels,
    ground_truth,
):
    cursor = connection.cursor()

    review_rows = []
    interaction_rows = []

    for review_id in range(1, TOTAL_REVIEWS + 1):
        customer_id = random.choice(customers)
        product_id, product_name = random.choice(products)
        channel_id = random.choice(channels)

        theme = choose_theme()
        sentiment = random_sentiment()

        feedback = generate_feedback(
            theme,
            sentiment,
            product_name,
        )

        if sentiment == "POSITIVE":
            rating = random.randint(4, 5)
        elif sentiment == "NEUTRAL":
            rating = 3
        else:
            rating = random.randint(1, 2)

        review_date = random_date()

        review_rows.append(
            (
                review_id,
                customer_id,
                product_id,
                channel_id,
                rating,
                feedback,
                review_date,
            )
        )

        interaction_rows.append(
            (review_id, review_id, review_date)
        )

        ground_truth.append(
            (review_id, sentiment, theme)
        )

    cursor.executemany(
        """
        INSERT INTO reviews
            (
                review_id,
                customer_id,
                product_id,
                channel_id,
                rating,
                review_text,
                review_date
            )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        review_rows,
    )

    # FIX: interactions has source foreign keys, not customer_id,
    # product_id, or channel_id.
    cursor.executemany(
        """
        INSERT INTO interactions (
            interaction_id,
            review_id,
            survey_response_id,
            support_message_id,
            interaction_date
        )
        VALUES (?, ?, NULL, NULL, ?)
        """,
        [
            (interaction_id, review_id, interaction_date)
            for interaction_id, review_id, interaction_date
            in interaction_rows
        ],
    )

    connection.commit()

    print(f"Generated reviews: {len(review_rows):,}")


# ==================================================
# GENERATE SURVEY RESPONSES
# ==================================================

def generate_survey_responses(
    connection,
    customers,
    products,
    channels,
    surveys,
    ground_truth,
):
    cursor = connection.cursor()

    response_rows = []
    interaction_rows = []

    for response_id in range(
        1,
        TOTAL_SURVEY_RESPONSES + 1,
    ):
        interaction_id = TOTAL_REVIEWS + response_id

        customer_id = random.choice(customers)
        product_id, product_name = random.choice(products)
        channel_id = random.choice(channels)
        survey_id = random.choice(surveys)

        theme = choose_theme()
        sentiment = random_sentiment()

        feedback = generate_feedback(
            theme,
            sentiment,
            product_name,
        )

        response_date = random_date()

        response_rows.append(
            (
                response_id,
                customer_id,
                product_id,
                channel_id,
                survey_id,
                feedback,
                response_date,
            )
        )

        interaction_rows.append(
            (interaction_id, response_id, response_date)
        )

        ground_truth.append(
            (interaction_id, sentiment, theme)
        )

    cursor.executemany(
        """
        INSERT INTO survey_responses
            (
                response_id,
                customer_id,
                product_id,
                channel_id,
                survey_id,
                response_text,
                response_date
            )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        response_rows,
    )

    # FIX: link each interaction to its survey response.
    cursor.executemany(
        """
        INSERT INTO interactions (
            interaction_id,
            review_id,
            survey_response_id,
            support_message_id,
            interaction_date
        )
        VALUES (?, NULL, ?, NULL, ?)
        """,
        [
            (interaction_id, response_id, interaction_date)
            for interaction_id, response_id, interaction_date
            in interaction_rows
        ],
    )

    connection.commit()

    print(
        f"Generated survey responses: {len(response_rows):,}"
    )


# ==================================================
# GENERATE SUPPORT MESSAGES
# ==================================================

def generate_support_messages(
    connection,
    customers,
    products,
    channels,
    ground_truth,
):
    cursor = connection.cursor()

    message_rows = []
    interaction_rows = []

    start_interaction_id = (
        TOTAL_REVIEWS
        + TOTAL_SURVEY_RESPONSES
    )

    for message_id in range(
        1,
        TOTAL_SUPPORT_MESSAGES + 1,
    ):
        interaction_id = start_interaction_id + message_id

        customer_id = random.choice(customers)
        product_id, product_name = random.choice(products)
        channel_id = random.choice(channels)

        theme = choose_theme()
        sentiment = random_sentiment()

        feedback = generate_feedback(
            theme,
            sentiment,
            product_name,
        )

        message_date = random_date()

        # FIX: these fields are required by the database schema.
        conversation_id = f"CONV-{message_id:07d}"
        sender_type = "CUSTOMER"

        message_rows.append(
            (
                message_id,
                customer_id,
                product_id,
                channel_id,
                conversation_id,
                feedback,
                message_date,
                sender_type,
            )
        )

        interaction_rows.append(
            (interaction_id, message_id, message_date)
        )

        ground_truth.append(
            (interaction_id, sentiment, theme)
        )

    cursor.executemany(
        """
        INSERT INTO support_messages
            (
                message_id,
                customer_id,
                product_id,
                channel_id,
                conversation_id,
                message_text,
                message_date,
                sender_type
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        message_rows,
    )

    # FIX: use the support_message_id foreign key.
    cursor.executemany(
        """
        INSERT INTO interactions (
            interaction_id,
            review_id,
            survey_response_id,
            support_message_id,
            interaction_date
        )
        VALUES (?, NULL, NULL, ?, ?)
        """,
        [
            (interaction_id, message_id, interaction_date)
            for interaction_id, message_id, interaction_date
            in interaction_rows
        ],
    )

    connection.commit()

    print(
        f"Generated support messages: {len(message_rows):,}"
    )


# ==================================================
# VALIDATE GENERATED DATA
# ==================================================

def validate_generated_data(connection):
    cursor = connection.cursor()

    expected_counts = {
        "customers": TOTAL_CUSTOMERS,
        "products": len(PRODUCTS),
        "channels": len(CHANNELS),
        "surveys": 8,
        "reviews": TOTAL_REVIEWS,
        "survey_responses": TOTAL_SURVEY_RESPONSES,
        "support_messages": TOTAL_SUPPORT_MESSAGES,
        "interactions": TOTAL_INTERACTIONS,
        "themes": len(THEMES),
        "sentiment_labels": len(SENTIMENTS),
    }

    print("\n========== RECORD COUNT VALIDATION ==========")

    failed = False

    for table, expected in expected_counts.items():
        actual = cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        passed = actual == expected

        print(
            f"{'PASS' if passed else 'FAIL'} | "
            f"{table}: {actual:,} (expected {expected:,})"
        )

        if not passed:
            failed = True

    invalid_interactions = cursor.execute(
        """
        SELECT COUNT(*)
        FROM interactions
        WHERE
            (
                (review_id IS NOT NULL)
                + (survey_response_id IS NOT NULL)
                + (support_message_id IS NOT NULL)
            ) != 1
        """
    ).fetchone()[0]

    print(
        f"{'PASS' if invalid_interactions == 0 else 'FAIL'} | "
        f"Invalid interaction source links: {invalid_interactions}"
    )

    if invalid_interactions:
        failed = True

    foreign_key_errors = cursor.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    print(
        f"{'PASS' if not foreign_key_errors else 'FAIL'} | "
        f"Foreign-key violations: {len(foreign_key_errors)}"
    )

    if foreign_key_errors:
        failed = True

    # Validate ratings are within the allowed range.
    invalid_ratings = cursor.execute(
        """
        SELECT COUNT(*)
        FROM reviews
        WHERE rating < 1 OR rating > 5
        """
    ).fetchone()[0]

    print(
        f"{'PASS' if invalid_ratings == 0 else 'FAIL'} | "
        f"Invalid review ratings: {invalid_ratings}"
    )

    if invalid_ratings:
        failed = True

    # Validate sentiment and theme labels in the separate ground-truth file.
    if GROUND_TRUTH_PATH.exists():
        with open(
            GROUND_TRUTH_PATH,
            "r",
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.DictReader(file)
            truth_rows = list(reader)

        expected_truth_count = TOTAL_INTERACTIONS

        truth_count_passed = (
            len(truth_rows) == expected_truth_count
        )

        print(
            f"{'PASS' if truth_count_passed else 'FAIL'} | "
            f"Ground-truth rows: {len(truth_rows):,} "
            f"(expected {expected_truth_count:,})"
        )

        if not truth_count_passed:
            failed = True

        valid_sentiments = set(SENTIMENTS)
        valid_themes = {theme for theme, _ in THEMES}

        invalid_labels = sum(
            1
            for row in truth_rows
            if row["true_sentiment"] not in valid_sentiments
            or row["true_theme"] not in valid_themes
        )

        print(
            f"{'PASS' if invalid_labels == 0 else 'FAIL'} | "
            f"Invalid ground-truth labels: {invalid_labels}"
        )

        if invalid_labels:
            failed = True

    else:
        print("FAIL | Ground-truth file was not found.")
        failed = True

    if failed:
        raise RuntimeError(
            "Data validation failed. Review the validation output."
        )

    print("\nALL DATA VALIDATION CHECKS PASSED")


# ==================================================
# MAIN
# ==================================================

def main():
    print("==============================================")
    print("       CUSTOMERPULSE AI DATA GENERATOR")
    print("==============================================")

    print(f"Seed: {SEED}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Database path: {DB_PATH}")
    print(f"Expected interactions: {TOTAL_INTERACTIONS:,}")

    # Prevent accidental duplicate generation.
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as check_connection:
            table_exists = check_connection.execute(
                """
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'interactions'
                """
            ).fetchone()[0]

            if table_exists:
                existing_count = check_connection.execute(
                    "SELECT COUNT(*) FROM interactions"
                ).fetchone()[0]

                if existing_count > 0:
                    raise RuntimeError(
                        "\nThe target database already contains "
                        "interaction records.\n"
                        f"Database: {DB_PATH}\n"
                        "Use an empty database or configure "
                        "CUSTOMERPULSE_OUTPUT_DIR to use a fresh "
                        "output directory."
                    )

    connection = get_connection()
    ground_truth = []

    try:
        print("\nGenerating reference data...")

        generate_reference_data(connection)

        (
            customers,
            products,
            channels,
            surveys,
        ) = load_reference_ids(connection)

        if not customers:
            raise RuntimeError("No customers were found.")

        if not products:
            raise RuntimeError("No products were found.")

        if not channels:
            raise RuntimeError("No channels were found.")

        if not surveys:
            raise RuntimeError("No surveys were found.")

        print("\nGenerating reviews...")

        generate_reviews(
            connection,
            customers,
            products,
            channels,
            ground_truth,
        )

        print("\nGenerating survey responses...")

        generate_survey_responses(
            connection,
            customers,
            products,
            channels,
            surveys,
            ground_truth,
        )

        print("\nGenerating support messages...")

        generate_support_messages(
            connection,
            customers,
            products,
            channels,
            ground_truth,
        )

        print("\nExporting ground truth...")

        export_ground_truth(ground_truth)

        print("\nValidating generated data...")

        validate_generated_data(connection)

        print("\n==============================================")
        print("DATA GENERATION COMPLETED SUCCESSFULLY")
        print("==============================================")
        print(f"Database: {DB_PATH}")
        print(f"Ground truth: {GROUND_TRUTH_PATH}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()