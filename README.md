CustomerPulse AI — Customer Feedback Intelligence System

An AI-powered customer feedback analytics prototype that analyzes synthetic customer interactions to identify sentiment, classify feedback themes, and explore customer feedback through an interactive dashboard.

Overview

Customer feedback can contain valuable information about product quality, delivery experiences, pricing, and customer support. However, manually reviewing large volumes of feedback can be time-consuming.

CustomerPulse AI demonstrates how machine learning can help organize and analyze feedback using text classification, data visualization, and an interactive analytics dashboard.

Important: This project uses synthetic data. Its results do not establish how well the models will perform on genuine customer feedback.

Features

- Customer feedback analytics: Explore customer interactions from surveys, product reviews, and support messages.
- Sentiment classification: Predict sentiment using a trained machine learning model.
- Theme classification: Assign feedback to a predicted theme.
- Interactive dashboard: Explore metrics and visualizations through Streamlit.
- Filtering: Filter interactions by product and channel.
- Feedback search: Search feedback using a case-insensitive text search.
- Visual analytics: Explore predicted sentiment, predicted themes, and feedback volume over time.
- Individual predictions: Enter new feedback and view predicted sentiment, theme, and available confidence estimates.
- Model evaluation: Display evaluation metrics from a saved JSON report.
- CSV export: Download filtered feedback records.
- Data validation: Validate dataset integrity and reproducibility using the project's validation scripts.

Technology Stack

Technology| Purpose
Python| Main programming language
Streamlit| Interactive dashboard
SQLite| Relational data storage
Pandas| Data loading and processing
NumPy| Numerical computing
Scikit-learn| Machine learning and text classification
TF-IDF| Text feature extraction
Logistic Regression| Sentiment and theme classification
Joblib| Saving and loading trained models
Plotly| Interactive charts
Pytest| Automated testing

Project Structure

The following is the expected high-level structure. Confirm the actual filenames in your repository before finalizing this section.

coding challenge/
├── app/
│   ├── dashboard/
│   │   └── dashboard.py
│   └── validation/
│       ├── validate_data.py
│       ├── detect_anomalies.py
│       └── test_reproducibility.py
├── data_fresh/
│   ├── customerpulse.db
│   └── ground_truth/
│       └── ground_truth.csv
├── models/
│   ├── sentiment_model.joblib
│   └── theme_model.joblib
├── reports/
│   └── model_evaluation.json
├── tests/
│   └── test_customerpulse.py
├── README.md
├── PROMPTS.md
├── requirements.txt
└── .gitignore

Other project files may exist, including data-generation and model-training scripts.

Dataset

The project uses synthetic customer interactions generated with the configured seed:

"20261022"

The previously validated dataset contained the following records:

Dataset component| Record count
Customers| 5,000
Products| 20
Channels| 5
Surveys| 8
Reviews| 25,000
Survey responses| 25,000
Support messages| 20,000
Interactions| 70,000
Themes| 10
Sentiment labels| 3
Ground-truth records| 70,000

These are previously reported counts. Rerun the project's validation scripts to confirm the current files still match them.

Data quality and limitations

The dataset was designed to support testing and demonstration of the feedback analytics pipeline.

Previous validation reported zero foreign-key violations and zero invalid interaction links, ratings, labels, or themes.

An earlier text-quality check also identified substantial repetition: approximately 1,130 unique messages across 70,000 records. Consequently, the dataset has limited text diversity.

Synthetic records and repeated messages can make model evaluation appear stronger than performance on diverse, genuine customer feedback. This limitation should be considered when interpreting results.

Machine Learning

The project uses TF-IDF text features and Logistic Regression classifiers for two tasks:

1. Sentiment classification.
2. Feedback theme classification.

The trained models are stored as Joblib artifacts.

Previously reported evaluation results

Model| Accuracy| Macro F1-score
Sentiment classification| 74.92%| 71.93%
Theme classification| 92.36%| 93.37%

These figures were reported during earlier development and must be checked against the current evaluation report before being treated as final results.

The models were evaluated on synthetic data. These metrics must not be interpreted as verified performance on real-world customer feedback.

Installation and Setup

Prerequisites

- Python version compatible with the project's dependencies.
- Git.
- Visual Studio Code or another Python development environment.

1. Clone the repository

After pushing the project to GitHub, clone it using:

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd "<YOUR_PROJECT_DIRECTORY>"

Replace the placeholders with your actual repository URL and directory name.

2. Create a virtual environment

Windows PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

If you already have a compatible, working virtual environment, you can activate that instead.

3. Install dependencies

If "requirements.txt" has been verified:

python -m pip install -r requirements.txt

Use package versions compatible with the project's Python version and saved model artifacts.

4. Verify required files

The dashboard expects these files at the configured locations:

data_fresh/customerpulse.db
models/sentiment_model.joblib
models/theme_model.joblib
reports/model_evaluation.json

The ground-truth CSV and validation scripts are also needed for the corresponding validation workflows.

Make sure the required artifacts are included in the repository or provided through a documented setup process.

Run the Dashboard

From the project root, activate the working virtual environment and run:

python -m streamlit run app\dashboard\dashboard.py

Open the local address displayed by Streamlit in your browser.

Testing and Validation

Run these commands from the project root in the appropriate Python environment.

Automated tests

python -m pytest -v

Data validation

python -m app.validation.validate_data

Anomaly detection

python -m app.validation.detect_anomalies

Reproducibility

python -m app.validation.test_reproducibility

These commands assume the corresponding modules exist at the documented paths. Confirm their names against the actual repository before publishing this README.

Investigate any failures rather than assuming the project is ready for release.

Deployment

The dashboard can be deployed to a compatible Streamlit hosting platform after the application and dependencies have been verified.

Before deployment:

1. Confirm that the required database and trained models are available to the hosted application.
2. Confirm that all file paths work in the hosting environment.
3. Verify the supported Python version and package dependencies.
4. Ensure the application does not depend on files available only on your local computer.
5. Check repository and hosting-platform file-size limits.
6. Remove secrets and sensitive information.
7. Test the deployed application using its public URL.

Deployment is complete only after the hosted application has been tested successfully.

Responsible Use and Limitations

- The dataset is synthetic, not genuine customer feedback.
- The dataset contains repeated messages and limited text diversity.
- Model performance on synthetic data may not generalize to real-world data.
- Predicted sentiment and themes can be incorrect.
- Confidence estimates are model probability estimates, not guarantees of correctness.
- Predictions should be reviewed before being used for business decisions.
- The application is a prototype, not a validated production decision-making system.

AI-Assisted Development

AI tools were used to assist with development-related activities. The accompanying "PROMPTS.md" file documents relevant development prompts and their intended purposes.

AI-generated code and suggestions must be reviewed, tested, and understood before use. See "PROMPTS.md" for the development prompt record.

Future Improvements

Potential improvements include:

- Increasing synthetic text diversity.
- Evaluating the models on appropriately obtained real-world data.
- Improving test coverage.
- Adding model monitoring and error analysis.
- Improving deployment automation.
- Adding more detailed data quality reporting.
- Improving accessibility and dashboard usability.

License

Choose an appropriate open-source license before publishing this repository. Do not imply that the project is licensed for reuse until a license has been selected and added.

Author

Alahari Govinda Sai Vigneswar

CustomerPulse AI — Customer Feedback Intelligence System