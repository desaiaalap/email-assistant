# Data Pipeline

## Introduction

The MailMate data pipeline processes email data from the Enron dataset to prepare it for training and validation. This pipeline handles data acquisition, preprocessing, validation, versioning, and anomaly detection.

## Dataset Information

The dataset used for this project is the **Enron Email Dataset**, a publicly available collection of **~500,000 emails** from the Enron Corporation. It is widely used for **Natural Language Processing (NLP)** tasks such as **email summarization, classification, and response generation**. The dataset contains structured fields, which are processed for model training and evaluation.

### **Data Sources**

- **Enron Email Dataset:** [Enron Dataset Link](https://www.cs.cmu.edu/~enron/)
- **Additional APIs:** Gmail API (for real-time email processing and integration)

### **Dataset Overview**

| **Attribute**    | **Details**                                                                      |
| ---------------- | -------------------------------------------------------------------------------- |
| **Dataset Name** | Enron Email Dataset                                                              |
| **Records**      | ~500,000 emails                                                                  |
| **Size**         | 1.7GB                                                                            |
| **Format**       | Plain text files                                                                 |
| **Fields**       | Sender, Recipient, Subject, Body, Date                                           |
| **Language**     | English                                                                          |
| **Usage**        | Training and fine-tuning NLP models for summarization and draft reply generation |

### **Data Card**

| **Variable Name** | **Role**   | **Type**      | **Description**                            | **Missing Values** |
| ----------------- | ---------- | ------------- | ------------------------------------------ | ------------------ |
| **Email_ID**      | Identifier | String        | Unique identifier for each email           | No                 |
| **Sender**        | Feature    | String        | Email address of the sender                | No                 |
| **Recipient(s)**  | Feature    | String (List) | Email addresses of the recipients          | Yes (Partial)      |
| **Subject**       | Feature    | String        | Subject line of the email                  | Yes (Few)          |
| **Body**          | Feature    | Text          | Full email content                         | No                 |
| **Date**          | Timestamp  | DateTime      | Date and time the email was sent           | No                 |
| **Attachments**   | Metadata   | String (List) | Names of attached files                    | Yes (Mostly)       |
| **Thread_ID**     | Identifier | String        | Identifies if an email is part of a thread | Yes (Partial)      |
| **Reply-To**      | Metadata   | String        | Indicates whether an email is a reply      | Yes (Few)          |

The dataset is **cleaned, preprocessed, and structured** to remove redundant metadata, normalize text, and extract meaningful insights for model training.

### **Data Rights and Privacy**

- The **Enron Email Dataset** is **publicly available** for research purposes.
- Any real-world user data will be accessed **only via API** with explicit **user consent**.
- **GDPR-compliant** security measures will be followed to ensure data privacy and compliance with international regulations.

## Installation & Prerequisites

### Prerequisites

1. **git** installed on your machine.
2. **Python == 3.11** installed (check using `python --version`).
3. **Docker** daemon/desktop installed and running (for containerizing the Airflow pipeline).

### User Installation

1. **Clone** the repository:

   ```bash
   git clone https://github.com/pshkrh/email-assistant.git
   cd email-assistant
   ```

2. **Check Python version** (3.11):

   ```bash
    python --version
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure DVC Setup**:

   - Create a Google Cloud Storage Bucket, follow this (https://www.mlwithramin.com/blog/dvc-lab1)
   - Save the credentials.json file at your desired location
   - In Terminal, at the root of the project i.e., email-assistant/, enter

   ```bash
     dvc init
   ```

   ```bash
     dvc remote add -d <desired_remote_name> gs://<your_bucket_name>
   ```

   ```bash
     dvc remote modify <created_desired_remote_name> credentialpath <your_credentials.json_path_relative_to_email_assitant/>
   ```

5. **Run Airflow**:

   - Enter the following to your terminal from root_directory i.e., email-assistant/

   ```bash
   echo -e "AIRFLOW_UID=$(id -u)" > .env
   ```

   - FOR WINDOWS: Create a file called .env in the root folder same as docker-compose.yaml and set the user as follows:

   ```bash
   AIRFLOW_UID=50000
   ```

   - Create GMAIL API Oauth client and download its credential.json (Note: To replicate we need to add your email address to test user so first please contact us to add you as a user)

     - Select Application as Desktop and give scope of GmailAPIService (https://mail.google.com/), Follow this (https://support.google.com/googleapi/answer/6158849?hl=en)

     - Download the credentials as json and set them in .env file as shown in .env-sample file, key=value without ""

     - Code to generate refresh token, email-assistant/data_pipeline/gmail_refresh_token.py

     - You can skip creating GMAIL API Oauth client if you don't want to send email notifications, it will log error in anomaly task.

   - Initialize Database

   ```bash
   docker compose up airflow-init
   ```

   - Run Container

   ```bash
   docker compose up --build
   ```

6. **Run the DAG in Airflow**:

   - Keep watch for this line in terminal

   ```bash
   app-airflow-webserver-1  | 127.0.0.1 - - [17/Feb/2023:09:34:29 +0000] "GET /health HTTP/1.1" 200 141 "-" "curl/7.74.0"
   ```

   - Log into Airflow UI at **localhost:8080** using

   ```bash
    user:airflow
    password:airflow
   ```

   - Run the DAG by clicking on the play button on the right side of the window once you see **datapipeline**.

   - Task performance can be time consuming depending on the resources provided to docker.

7. **Shutdown** containers:

   ```bash
   docker compose down
   ```

8. **Store Data**:

   - From root email-assistant/

   ```bash
   dvc add data_pipeline/data/enron_emails.csv
   ```

   - Use dvc push to store it to your GCP bucket.

9. **Tests** :
   - To run tests from root directory email_assistant/
   ```bash
   pytest data_pipeline/tests/ -v
   ```
   - For individual tests replace \* with test file name from data_pipeline/tests/

## Data Pipeline Overview

MailMate's **data pipeline** is designed to handle **end-to-end email processing**, ensuring efficient data ingestion, transformation, and model training. The pipeline is orchestrated using **Apache Airflow**, which automates workflows, maintains scalability, and ensures fault tolerance. The system follows **MLOps best practices**, including **data validation, version control, anomaly detection, and automated model retraining**.

## Directory Structure

The `data_pipeline` directory contains all components related to email data processing:

```
data_pipeline/
├── __init__.py                  # Package initialization
├── pytest.ini                   # Pytest configuration
├── scripts/                     # Core processing scripts
│   ├── __init__.py
│   ├── clean_and_parse_dates.py # Date field processing
│   ├── create_logger.py         # Logging utility
│   ├── data_bias_data_creation.py # Creates data slices for bias detection
│   ├── data_clean.py            # Main data cleaning script
│   ├── data_pipeline            # Pipeline orchestration
│   ├── data_quality_anomaly.py  # Anomaly detection
│   ├── data_quality_expectations.py # Data validation expectations
│   ├── data_quality_setup.py    # Great Expectations setup
│   ├── data_quality_validation.py # Data validation
│   ├── dataframe.py             # DataFrame processing utilities
│   ├── download_dataset.py      # Dataset download from source
│   ├── extract_dataset.py       # Dataset extraction
│   ├── get_project_root.py      # Path utility
│   └── google_refresh_token.py  # OAuth token management
└── tests/                       # Test suite
    ├── __init__.py
    ├── conftest.py              # Test configuration
    ├── test_clean_and_parse_dates.py
    ├── test_create_logger.py
    ├── test_data_quality_anomaly.py
    ├── test_data_quality_expectations.py
    ├── test_data_quality_setup.py
    ├── test_data_quality_validation.py
    ├── test_dataframe.py
    ├── test_download_dataset.py
    └── test_extract_dataset.py
```

### Key Scripts

- **download_dataset.py**: Downloads the Enron dataset from the source URL
- **extract_dataset.py**: Extracts the compressed dataset archive
- **dataframe.py**: Processes email files into a structured DataFrame
- **data_clean.py**: Performs extensive data cleaning and normalization
- **clean_and_parse_dates.py**: Specifically handles date field parsing and standardization
- **data_quality_*.py**: Suite of scripts for data validation and anomaly detection

### Data Quality Pipeline

The data quality framework uses **Great Expectations** and includes:

1. **data_quality_setup.py**: Sets up the validation environment
2. **data_quality_expectations.py**: Defines validation rules for the dataset
3. **data_quality_validation.py**: Performs validation against defined expectations
4. **data_quality_anomaly.py**: Detects and reports anomalies, sending alerts if needed

### Tests

Comprehensive test coverage for all script components using pytest:

- Tests for all data processing functions
- Tests for data quality validation
- Tests for utility modules

## Contact

For questions or collaboration:

- Open an issue on this GitHub repo.
- Or reach out to any of the team members directly.
