-- CustomerPulse: Database Schema
-- Database: SQLite

PRAGMA foreign_keys = ON;

-- 1. Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    email TEXT,
    region TEXT,
    created_at TEXT NOT NULL
);

-- 2. Products
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 3. Channels
CREATE TABLE IF NOT EXISTS channels (
    channel_id INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE
);

-- 4. Surveys
CREATE TABLE IF NOT EXISTS surveys (
    survey_id INTEGER PRIMARY KEY,
    survey_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT
);

-- 5. Survey responses
CREATE TABLE IF NOT EXISTS survey_responses (
    response_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    survey_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    response_date TEXT NOT NULL,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id),
    FOREIGN KEY (survey_id) REFERENCES surveys(survey_id)
);

-- 6. Product reviews
CREATE TABLE IF NOT EXISTS reviews (
    review_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT NOT NULL,
    review_date TEXT NOT NULL,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
);

-- 7. Support messages
CREATE TABLE IF NOT EXISTS support_messages (
    message_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER,
    channel_id INTEGER NOT NULL,
    conversation_id TEXT NOT NULL,
    message_text TEXT NOT NULL,
    message_date TEXT NOT NULL,
    sender_type TEXT NOT NULL
        CHECK (sender_type IN ('CUSTOMER', 'AGENT')),

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
);

-- 8. Standardized interactions
-- Each interaction must refer to exactly one source record.
CREATE TABLE IF NOT EXISTS interactions (
    interaction_id INTEGER PRIMARY KEY,
    survey_response_id INTEGER UNIQUE,
    review_id INTEGER UNIQUE,
    support_message_id INTEGER UNIQUE,
    interaction_date TEXT NOT NULL,

    CHECK (
        (survey_response_id IS NOT NULL)
        + (review_id IS NOT NULL)
        + (support_message_id IS NOT NULL) = 1
    ),

    FOREIGN KEY (survey_response_id)
        REFERENCES survey_responses(response_id),

    FOREIGN KEY (review_id)
        REFERENCES reviews(review_id),

    FOREIGN KEY (support_message_id)
        REFERENCES support_messages(message_id)
);

-- 9. Themes
CREATE TABLE IF NOT EXISTS themes (
    theme_id INTEGER PRIMARY KEY,
    theme_name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1))
);

-- 10. Sentiment labels
CREATE TABLE IF NOT EXISTS sentiment_labels (
    sentiment_label_id INTEGER PRIMARY KEY,
    label_name TEXT NOT NULL UNIQUE
        CHECK (
            label_name IN (
                'POSITIVE',
                'NEUTRAL',
                'NEGATIVE'
            )
        )
);

-- 11. Theme assignments
-- One interaction can have multiple themes.
CREATE TABLE IF NOT EXISTS interaction_themes (
    interaction_id INTEGER NOT NULL,
    theme_id INTEGER NOT NULL,
    confidence REAL
        CHECK (
            confidence IS NULL
            OR (confidence >= 0 AND confidence <= 1)
        ),

    PRIMARY KEY (interaction_id, theme_id),

    FOREIGN KEY (interaction_id)
        REFERENCES interactions(interaction_id),

    FOREIGN KEY (theme_id)
        REFERENCES themes(theme_id)
);

-- 12. Sentiment predictions
-- Predictions are kept separate from source text.
CREATE TABLE IF NOT EXISTS sentiment_predictions (
    prediction_id INTEGER PRIMARY KEY,
    interaction_id INTEGER NOT NULL,
    sentiment_label_id INTEGER NOT NULL,
    model_version TEXT NOT NULL,
    confidence REAL NOT NULL
        CHECK (confidence BETWEEN 0 AND 1),
    predicted_at TEXT NOT NULL,

    FOREIGN KEY (interaction_id)
        REFERENCES interactions(interaction_id),

    FOREIGN KEY (sentiment_label_id)
        REFERENCES sentiment_labels(sentiment_label_id)
);

-- 13. Recommended action items
CREATE TABLE IF NOT EXISTS action_items (
    action_item_id INTEGER PRIMARY KEY,
    theme_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL
        CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (
            status IN (
                'OPEN',
                'IN_PROGRESS',
                'COMPLETED',
                'CANCELLED'
            )
        ),
    created_at TEXT NOT NULL,

    FOREIGN KEY (theme_id)
        REFERENCES themes(theme_id)
);

-- Indexes to improve common queries.
CREATE INDEX IF NOT EXISTS idx_responses_customer
    ON survey_responses(customer_id);

CREATE INDEX IF NOT EXISTS idx_reviews_product_date
    ON reviews(product_id, review_date);

CREATE INDEX IF NOT EXISTS idx_messages_customer_date
    ON support_messages(customer_id, message_date);

CREATE INDEX IF NOT EXISTS idx_interactions_date
    ON interactions(interaction_date);

CREATE INDEX IF NOT EXISTS idx_predictions_interaction
    ON sentiment_predictions(interaction_id);

CREATE INDEX IF NOT EXISTS idx_interaction_themes_theme
    ON interaction_themes(theme_id);