CustomerPulse – Data Dictionary

 1. About the Project

CustomerPulse is a project that brings customer feedback from different sources into one place. Customers share their opinions through product reviews, survey responses, and support messages. Looking at this feedback together helps us understand what customers like, what problems they face, and what needs to be improved.

For this project, I'm using Python to generate synthetic customer data and SQLite to store and manage it. The generated dataset contains 70,000 customer interactions, which can later be used to study sentiment, identify common feedback themes, and suggest improvements.

 2. Database Tables

The database is divided into separate tables so that customer details, products, feedback, and analysis results can be managed without putting everything into one large table.

| Table Name | What it stores |
|---|---|
| `customers` | Basic details of the synthetic customers. |
| `products` | The products customers give feedback about. |
| `channels` | The channels through which customers share feedback. |
| `surveys` | Details of the surveys used to collect feedback. |
| `survey_responses` | Answers submitted by customers through surveys. |
| `reviews` | Reviews written by customers about products. |
| `support_messages` | Messages sent by customers when they need help or report a problem. |
| `interactions` | A common record for connecting feedback from different sources. |
| `themes` | Categories used to group similar feedback, such as delivery issues or product quality. |
| `sentiment_labels` | The sentiment categories used in the project. |
| `interaction_themes` | Connects customer interactions with the themes identified in them. |
| `sentiment_predictions` | Stores sentiment results produced by the analysis or prediction process. |
| `action_items` | Stores possible actions that could help address customer problems. |

3. Important Entities

Customer

The `customers` table contains the customers created for testing the workflow. The records are synthetic and do not represent real customers.

- `customer_id` – Unique ID assigned to each customer.
- `customer_name` – Name generated for the customer.
- `created_at` – Date and time when the customer record was created.

### Product

The `products` table contains the products associated with customer feedback.

- `product_id` – Unique product ID.
- `product_name` – Name of the product.
- `category` – Category to which the product belongs.
- `created_at` – Date and time when the product record was created.

 Channel

The `channels` table identifies where the feedback came from. Keeping channel information separate makes it easier to compare feedback received through different sources.

 Survey and Survey Response

The `surveys` table stores survey details, while `survey_responses` stores the answers submitted by customers. Each response includes the feedback text and the date it was submitted.

 Review

The `reviews` table stores product reviews written by customers. The review text and date can be used to understand customer opinions about different products.

 Support Message

The `support_messages` table contains messages from customers who contact support. These messages can help identify recurring complaints and areas where the service needs improvement.

 Interaction

The `interactions` table brings the three feedback sources together. Each interaction points to one source record: a review, a survey response, or a support message. This makes it easier to analyze different types of feedback using a common structure.

 Theme

The `themes` table contains the categories used to group similar customer comments. For example, feedback about late deliveries can be grouped under a delivery-related theme.

 Sentiment Label

The `sentiment_labels` table defines the sentiment categories used in the project:

- `POSITIVE`
- `NEUTRAL`
- `NEGATIVE`

These labels help describe the general tone of a customer's feedback.

 Action Item

The `action_items` table is intended to store suggested actions based on the feedback analysis. For example, repeated complaints about delayed deliveries could lead to an action to review delivery performance.

4. Dataset Summary

The current synthetic dataset contains the following records:

| Data | Number of Records |
|---|---:|
| Customers | 5,000 |
| Products | 20 |
| Channels | 5 |
| Surveys | 8 |
| Reviews | 25,000 |
| Survey responses | 25,000 |
| Support messages | 20,000 |
| Total interactions | 70,000 |
| Ground-truth records | 70,000 |

The data is generated using a fixed random seed (`20261022`). The aim is to make it possible to reproduce the dataset and test the workflow consistently.

 5. Ground-Truth Data

The reference labels are stored separately in `data/ground_truth/ground_truth.csv`.

The file contains three columns:

- `interaction_id` – Identifies the interaction associated with the reference label.
- `true_sentiment` – The expected sentiment label.
- `true_theme` – The expected feedback theme.

Keeping these labels separate from the model's input data is important. Otherwise, the model could accidentally use the answers it is supposed to predict, which would make the evaluation unreliable.

6. Data Validation

I have added a validation script at `app/validation/validate_data.py` to check the generated data before moving on to the analysis.

The current checks cover:

- Whether the tables contain the expected number of records.
- Whether selected required fields contain missing values.
- Whether database foreign-key relationships are valid.
- Whether every interaction points to exactly one feedback source.
- Whether the ground-truth file has the expected columns and number of records.
- Whether the ground-truth sentiment labels are valid.

These checks have passed for the dataset generated so far. Further checks are still needed for duplicate records, unusual or conflicting feedback, theme taxonomy violations, and reproducibility.