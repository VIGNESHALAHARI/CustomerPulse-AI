CustomerPulse AI — Customer Feedback Intelligence System

An AI-powered customer feedback analytics prototype that analyzes synthetic customer interactions to identify sentiment, classify feedback themes, and explore customer feedback through an interactive dashboard.

<p align="center">
  <a href="https://customerpulse-ai-dvlczpc6kldtnappabq4dfp.streamlit.app/">
    <strong>🚀 Live Demo</strong>
  </a>
  &nbsp; | &nbsp;
  <a href="https://github.com/VIGNESHALAHARI/CustomerPulse-AI">
    <strong>💻 GitHub Repository</strong>
  </a>
</p>---

📌 Overview

Customer feedback contains valuable information about product quality, delivery experiences, pricing, and customer support. However, manually reviewing large volumes of feedback can be time-consuming.

CustomerPulse AI demonstrates how machine learning can help organize and analyze customer feedback through text classification, data visualization, and an interactive analytics dashboard.

The application combines a Streamlit interface, SQLite data storage, and trained machine learning models to provide sentiment predictions, theme classification, and feedback exploration.

«Important: This project uses synthetic customer data. Its results do not establish how well the models will perform on genuine customer feedback.»

✨ Features

- Customer Feedback Analytics: Explore customer interactions from surveys, product reviews, and support messages.
- Sentiment Classification: Predict the sentiment of customer feedback using a trained machine learning model.
- Theme Classification: Assign feedback to a predicted theme.
- Interactive Dashboard: Explore metrics and visualizations through Streamlit.
- Filtering: Filter interactions by product and channel.
- Feedback Search: Search feedback using a case-insensitive text search.
- Visual Analytics: Explore predicted sentiment, predicted themes, and feedback volume over time.
- Individual Predictions: Enter new feedback and view predicted sentiment, theme, and available confidence estimates.
- Model Evaluation: Display evaluation metrics from a saved JSON report.
- CSV Export: Download filtered feedback records.
- Data Validation: Run validation scripts to assess dataset integrity, anomalies, and reproducibility.

🖥️ Live Application

Try CustomerPulse AI:
https://customerpulse-ai-dvlczpc6kldtnappabq4dfp.streamlit.app/

The application is deployed using Streamlit Community Cloud.

The live application should be evaluated as a demonstration prototype. Its predictions and analytics are based on synthetic data and should not be interpreted as verified business outcomes.

🛠️ Technology Stack

Technology| Purpose
Python| Main programming language
Streamlit| Interactive dashboard and application interface
SQLite| Relational data storage
Pandas| Data loading and processing
NumPy| Numerical computing
Scikit-learn| Machine learning and text classification
TF-IDF| Text feature extraction
Logistic Regression| Sentiment and theme classification
Joblib| Saving and loading trained models
Plotly| Interactive data visualization
Pytest| Automated testing

🧠 Machine Learning Approach

CustomerPulse AI uses text classification to analyze customer feedback.

1. Text Feature Extraction

TF-IDF (Term Frequency–Inverse Document Frequency) converts feedback text into numerical features that machine learning models can process.

2. Sentiment Classification

A trained Logistic Regression classifier predicts the sentiment associated with a feedback message.

3. Theme Classification

A separate trained Logistic Regression classifier predicts the theme associated with a feedback message.

4. Model Persistence

The trained models are saved as Joblib artifacts and loaded by the application for prediction.

The repository includes the following model files:

- "models/sentiment_model.joblib"
- "models/theme_model.joblib"

Model predictions depend on the training data and its characteristics. The synthetic dataset's repetition and limited text diversity may affect the reported evaluation results.

📊 Dataset

The project uses synthetically generated customer interaction data.

The configured generation seed was previously reported as "20261022".

The following counts were reported during earlier development and should be confirmed by running the current validation scripts.

Dataset Component| Previously Reported Records
Customers| 5,000
Products| 20
Channels| 5
Surveys| 8
Reviews| 25,000
Survey Responses| 25,000
Support Messages| 20,000
Interactions| 70,000
Themes| 10
Sentiment Labels| 3
Ground-Truth Records| 70,000

The repository contains generated datasets, SQLite databases, and ground-truth data used for analysis, evaluation, and validation.

Data Quality and Limitations

Previous validation reported:

- Zero foreign-key violations.
- Zero invalid interaction links.
- No invalid ratings, labels, or themes in the validated dataset.
- Approximately 1,130 unique messages across 70,000 records in an earlier text-quality analysis.

The relatively small number of unique messages indicates substantial repetition and limited text diversity.

Synthetic records and repeated messages can make model evaluation appear stronger than performance on diverse, genuine customer feedback. These limitations must be considered when interpreting the results.

📈 Previously Reported Model Evaluation

The following results were reported during earlier development. They must be verified against the current "reports/model_evaluation.json" file before being treated as final.

Model| Accuracy| Macro F1-Score
Sentiment Classification| 74.92%| 71.93%
Theme Classification| 92.36%| 93.37%

These metrics were obtained using synthetic data and do not establish model performance on real-world customer feedback.

The reported results should be interpreted alongside the dataset's limited text diversity, repeated messages, and evaluation methodology.

📁 Project Structure

The main files committed to the repository are organized as follows:

CustomerPulse-AI/
├── .streamlit/
│   └── config.toml
├── app/
│   ├── dashboard/
│   │   └── dashboard.py
│   ├── data_generation/
│   │   ├── export_data.py
│   │   ├── export_sql.py
│   │   └── generate_data.py
│   ├── database/
│   │   ├── init_db.py
│   │   └── schema.sql
│   ├── ml/
│   │   └── train_models.py
│   └── validation/
│       ├── analyze_data_quality.py
│       ├── analyze_text_quality.py
│       ├── create_anomaly_cases.py
│       ├── detect_anomalies.py
│       ├── test_reproducibility.py
│       ├── validate_data.py
│       └── validate_data_backup.py
├── data/
│   ├── evaluation/
│   ├── generated/
│   └── ground_truth/
├── data_fresh/
│   ├── customerpulse.db
│   └── ground_truth/
├── data_quality_test/
│   └── customerpulse.db
├── docs/
│   └── data_dictionary.md
├── models/
│   ├── sentiment_model.joblib
│   └── theme_model.joblib
├── reports/
│   └── model_evaluation.json
├── tests/
│   └── test_customerpulse.py
├── .gitignore
├── Prompts_used.txt
├── README.md
└── requirements.txt

The repository also contains additional generated CSV, JSON, and SQL files under "data/generated/".

🚀 Installation and Setup

Prerequisites

- Python compatible with the pinned dependencies.
- Git.
- A terminal such as Windows PowerShell or macOS/Linux Terminal.
- A Python development environment such as Visual Studio Code.

1. Clone the Repository

git clone https://github.com/VIGNESHALAHARI/CustomerPulse-AI.git
cd CustomerPulse-AI

2. Create a Virtual Environment

Windows PowerShell

python -m venv .venv
.\.venv\Scripts\Activate.ps1

If PowerShell prevents activation because of its execution policy, use an appropriate process-scoped policy or follow your organization's security guidance.

macOS/Linux

python -m venv .venv
source .venv/bin/activate

3. Install Dependencies

Install the packages specified in "requirements.txt":

python -m pip install -r requirements.txt

Use a Python version compatible with the pinned dependencies and the project's saved model artifacts.

4. Verify Required Files

The dashboard is configured to use the following files:

data_fresh/customerpulse.db
models/sentiment_model.joblib
models/theme_model.joblib
reports/model_evaluation.json

The ground-truth CSV and validation scripts are needed for the corresponding validation workflows.

Ensure the required files are present after cloning the repository.

▶️ Run the Dashboard Locally

From the repository root, activate the virtual environment and run:

python -m streamlit run app/dashboard/dashboard.py

Streamlit will display a local URL in the terminal. Open that address in your browser to access the application.

🧪 Testing and Validation

Run the commands from the repository root using a compatible Python environment.

Automated Tests

python -m pytest -v

Data Validation

python -m app.validation.validate_data

Anomaly Detection

python -m app.validation.detect_anomalies

Reproducibility Validation

python -m app.validation.test_reproducibility

These commands correspond to the validation modules included in the repository. If a command fails, investigate the error and its dependencies rather than assuming validation has passed.

☁️ Deployment

The application is deployed using Streamlit Community Cloud.

Live application:
https://customerpulse-ai-dvlczpc6kldtnappabq4dfp.streamlit.app/

Deployment configuration and dependencies should be kept consistent with the application's local setup.

For reproducible deployments:

1. Ensure all required application files are committed to GitHub.
2. Keep the dependency list updated.
3. Confirm that database and model paths work in the hosted environment.
4. Avoid dependencies on files available only on a developer's computer.
5. Keep secrets and sensitive information out of the repository.
6. Test the deployed application after code or dependency changes.

🔒 Responsible Use and Limitations

- The dataset is synthetic, not genuine customer feedback.
- The dataset contains repeated messages and limited text diversity.
- Model performance on synthetic data may not generalize to real-world data.
- Sentiment and theme predictions can be incorrect.
- Confidence estimates, when available, are model probability estimates rather than guarantees of correctness.
- Predictions should be reviewed before being used to inform business decisions.
- The application is a demonstration prototype, not a validated production decision-making system.

🤖 AI-Assisted Development

AI tools were used to assist with development-related activities.

The repository includes "Prompts_used.txt", which documents reusable development prompts and their intended purposes. The file should not be interpreted as an exact transcript of historical conversations unless it has been verified as such.

AI-generated code and suggestions should be reviewed, tested, and understood before use.

🔮 Future Improvements

Potential improvements include:

- Increasing the diversity of synthetic feedback text.
- Evaluating the models on appropriately obtained real-world data.
- Expanding automated test coverage.
- Adding more detailed model error analysis.
- Improving deployment automation.
- Enhancing data quality reporting.
- Improving dashboard accessibility and usability.
- Monitoring model behavior as new data becomes available.

📄 License

No open-source license has been specified in this repository.

A license should be selected and added before granting explicit reuse permissions. Until then, do not assume that the project is licensed for unrestricted reuse.

👨‍💻 Author

Alahari Govinda Sai Vigneswar

GitHub: https://github.com/VIGNESHALAHARI

---

CustomerPulse AI — Customer Feedback Intelligence System

An educational prototype demonstrating customer feedback analytics, text classification, and interactive data visualization using Python and machine learning.
