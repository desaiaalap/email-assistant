# Model Pipeline and Deployment

## Prerequisites and Environment Setup

Before deploying MailMate, you'll need to set up your development environment. This section will guide you through installing all necessary tools and dependencies.

### 1. Install Git

Git is required for version control and cloning the repository:

**For Windows:**

- Download and install Git from [git-scm.com](https://git-scm.com/download/win)
- Follow the installation wizard with default settings

**For macOS:**

- Install using Homebrew: `brew install git`
- Or download from [git-scm.com](https://git-scm.com/download/mac)

**For Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install git
```

Verify installation: `git --version`

### 2. Install Python 3.11

MailMate requires Python 3.11:

**For Windows:**

- Download Python 3.11 from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

**For macOS:**

```bash
brew install python@3.11
```

**For Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

Verify installation: `python --version` or `python3.11 --version`

### 3. Install Docker and Docker Compose

Docker is used for containerization:

**For Windows/macOS:**

- Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)

**For Linux (Ubuntu/Debian):**

```bash
# Install Docker
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install docker-ce

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Verify installation: `docker --version` and `docker-compose --version`

### 4. Install Google Cloud SDK (gcloud CLI)

The Google Cloud SDK is required for GCP deployments:

**For all platforms:**

- Download and install from [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)

**Alternatively, for macOS:**

```bash
brew install --cask google-cloud-sdk
```

**For Linux (Ubuntu/Debian):**

```bash
# Add the Cloud SDK distribution URI as a package source
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import the Google Cloud public key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Update and install the SDK
sudo apt update
sudo apt install google-cloud-sdk
```

After installation, initialize gcloud:

```bash
gcloud init
```

This will open a browser window for authentication. Follow the prompts to:

- Login with your Google account
- Select or create a GCP project
- Configure default region and zone

### 5. Install GitHub CLI

GitHub CLI is useful for managing GitHub repositories and secrets:

**For Windows:**

- Download from [cli.github.com](https://cli.github.com/)
- Follow installation wizard

**For macOS:**

```bash
brew install gh
```

**For Linux (Ubuntu/Debian):**

```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

Authenticate with GitHub:

```bash
gh auth login
```

Follow the interactive prompts to complete authentication.

### 6. Clone the Repository

Once all prerequisites are installed, clone the repository:

```bash
git clone https://github.com/yourusername/email-assistant.git
cd email-assistant
```

## Directory Structure

The `model_pipeline` directory contains all components of the AI model infrastructure:

```
model_pipeline/
├── Dockerfile                   # Docker container configuration
├── Dockerfile_validation        # Container for validation tasks
├── README.md                    # Documentation
├── bias_validation_requirements.txt  # Dependencies for bias validation
├── credentials/                 # API credential storage
│   ├── GoogleCloudCredential.json  # GCP service account key
│   ├── MailMateCredential.json     # OAuth credentials
│   └── user_tokens/                # User token storage
├── docker-compose.yaml          # Docker configuration
├── requirements.txt             # Primary dependencies
├── scripts/                     # Core model and API scripts
│   ├── bias_checker.py          # Bias detection and analysis
│   ├── config.py                # Configuration settings
│   ├── data_loader.py           # Data loading utilities
│   ├── db_connection.py         # Database connection handling
│   ├── db_helpers.py            # Database utility functions
│   ├── fetch_gmail_threads.py   # Main API server
│   ├── generate_gcp_metrics.py  # Metrics generation for monitoring
│   ├── get_project_root.py      # Path utility
│   ├── initialize_db.py         # Database initialization
│   ├── llm_generator.py         # Core LLM generation logic
│   ├── llm_ranker.py            # Output ranking system
│   ├── load_prompts.py          # Prompt template loading
│   ├── main.py                  # Entry point
│   ├── mlflow_config.py         # MLflow experiment tracking setup
│   ├── monitoring_api.py        # Performance monitoring endpoints
│   ├── output_verifier.py       # Output format validation
│   ├── performance_monitor.py   # User feedback monitoring
│   ├── populate_metrics.py      # Metrics population script
│   ├── prompt_update_demo.py    # Prompt optimization demo
│   ├── render_alternate_prompt.py  # Alternate prompt renderer
│   ├── render_criteria.py       # Ranking criteria renderer
│   ├── render_prompt.py         # Standard prompt renderer
│   ├── save_to_database.py      # Database storage utilities
│   ├── secret_manager.py        # Secrets management
│   ├── send_notification.py     # Email notification system
│   ├── sensitivity_analysis.py  # Model sensitivity testing
│   ├── setup_cloud_monitoring.sh # GCP monitoring setup
│   ├── setup_cloud_scheduler.sh # Scheduled tasks setup
│   ├── test_endpoints.py        # API endpoint testing
│   ├── update_database.py       # Database update utilities
│   └── validation.py            # Output validation
└── sensitivity_analysis_requirements.txt  # Dependencies for analysis
```

### Key Script Files

- **fetch_gmail_threads.py**: Core API server that processes email threads and generates AI responses
- **llm_generator.py**: Handles generation of summaries, action items, and replies using Vertex AI
- **llm_ranker.py**: Ranks multiple generated outputs to select the best one
- **output_verifier.py**: Ensures outputs meet formatting and quality requirements
- **performance_monitor.py**: Tracks user feedback and optimizes prompt strategies
- **initialize_db.py**: Sets up database schema for storing user preferences and feedback

### YAML Configuration Files

- **llm_generator_prompts.yaml**: Default generation prompt templates
- **llm_generator_prompts_alternate.yaml**: Alternative prompt templates for optimization
- **llm_ranker_criteria.yaml**: Criteria for ranking generated outputs
- **llm_output_structure.yaml**: Output format specifications

### Monitoring and Analysis

- **generate_gcp_metrics.py**: Creates Cloud Monitoring metrics for tracking performance
- **bias_checker.py**: Analyzes model outputs for potential biases across different data slices
- **sensitivity_analysis.py**: Tests model robustness to various inputs and prompt variations
- **monitoring_api.py**: API endpoints for monitoring system performance and optimization
- **test_endpoints.py**: Testing framework for API validation

### Database Management

- **db_connection.py**: Handles database connections with Cloud SQL
- **save_to_database.py**: Stores generated outputs and metadata
- **update_database.py**: Updates existing records with user feedback
- **db_helpers.py**: Utility functions for database operations

### Utilities

- **secret_manager.py**: Secure handling of API keys and credentials
- **send_notification.py**: Error notification system via email
- **mlflow_config.py**: Configuration for MLflow experiment tracking
- **config.py**: Central configuration settings
- **get_project_root.py**: Utility for finding project paths

### Deployment Scripts

- **setup_cloud_monitoring.sh**: Sets up GCP Cloud Monitoring for performance tracking
- **setup_cloud_scheduler.sh**: Configures scheduled jobs for optimization
- **setup_cicd.sh**: Sets up CI/CD pipeline for automated deployment
- **make_dash.sh** and **make_dash2.sh**: Creates monitoring dashboards

### Chrome Extension Files

The Chrome extension components are located in a separate directory:

```
extension/
├── background.js              # Background service worker
├── config.js                  # Configuration settings
├── content.js                 # Gmail page interaction
├── icon.png                   # Extension icon
├── logo.png                   # MailMate logo
├── manifest.json              # Extension manifest
├── popup.html                 # Extension popup UI
├── popup.js                   # Popup functionality
└── styles.css                 # UI styling
```

## Model Pipeline Overview

The MailMate email assistant employs a model pipeline using Google's Vertex AI services for generating summaries, action items, and draft replies from email content.

### Model Architecture

Our system utilizes a Gemini model (`gemini-1.5-flash-002`), which we selected after comparing performance across tasks, speed and cost. The model architecture includes:

- **LLM Generator**: Processes email content to generate multiple candidate outputs for each task
- **LLM Ranker**: Evaluates and ranks candidate outputs based on quality criteria
- **Output Verifier**: Ensures outputs meet structural requirements before delivering to users

### Performance Monitoring and Metrics

We track several key metrics to monitor model performance:

- **Positive Feedback Rate**: Percentage of positive and negative feedback
- **Task Performance Score**: Task-specific threshold for summaries, action items, and replies
- **Bias Detection**: Measurements across different data slices to ensure fairness

### Prompt Optimization and Strategy

We employ dynamic prompt optimization based on user feedback:

- **Default Strategy**: Initial prompt template for most users
- **Alternate Strategy**: Used when performance drops below threshold
- **User-Specific Optimization**: Sets strategies for individual users based on their recent feedback patterns

### Experiment Tracking

We use MLflow for experiment tracking, which allows:

- Logging of model parameters and metrics
- Comparison of different prompt strategies
- Logging of model artifacts
- Visualization of performance trends

### Bias Detection

Our system performs bias detection across data slices to ensure fairness:

- **Email Length Slicing**: Analyzes performance across short, medium, and long emails
- **Email Complexity Slicing**: Tests performance on emails of varying complexity
- **Sender Role Slicing**: Ensures consistent performance regardless of sender's role

The bias checking is run through `bias_checker.py` and results are tracked in MLflow. We adjusted the prompts based on its output to get more accurate results among its range.

### Sensitivity Analysis

We conduct sensitivity analysis to understand how the model responds to:

- **Input Perturbations**: Testing robustness to changes in email content
- **Prompt Variations**: Measuring impact of different prompt styles
- **Parameter Sensitivity**: Analyzing effects of temperature and token limits

The sensitivity analysis is implemented in `sensitivity_analysis.py`. Our model performed well on all the criterias.

## Cloud Deployment

Our project is deployed on Google Cloud Platform using Cloud Run, Cloud SQL, and MLflow for experiment tracking. The deployment is fully automated through GitHub Actions CI/CD pipeline.

### Deployment Architecture

- **Email Assistant API**: Runs on Cloud Run, processing email requests
- **MLflow Server**: Runs on Cloud Run for experiment tracking
- **Cloud SQL Database**: Stores user feedback and prompt optimization data
- **GCP Logging & Monitoring**: Tracks performance metrics and anomalies

### Monitoring and Alerts

The system includes comprehensive monitoring:

- **Cloud Monitoring Dashboard**: Visualizes key performance metrics
- **Log-based Metrics**: Tracks performance scores, processing times, and error rates
- **Automated Alerting**: Sends notifications when metrics drop below thresholds

### Automated Retraining

Our pipeline automatically updates prompt strategies when performance drops:

1. System monitors positive feedback rates and performance metrics
2. When metrics fall below threshold (70%), it switches to alternate strategies
3. Daily scheduled checks evaluate all users' performance
4. User-specific optimizations are made based on individual patterns

## Deployment Instructions

### Automatic Deployment Using CI/CD Script

For a fully automated deployment experience, follow these steps:

1. **Fork the Repository**: Fork this repository to your GitHub account

2. **Set Up Google Cloud Project**:

   If you don't have a GCP project yet:

   ```bash
   # Create a new GCP project
   gcloud projects create [PROJECT_ID] --name="MailMate Email Assistant"

   # Set it as the active project
   gcloud config set project [PROJECT_ID]

   # Enable billing (required for most GCP services)
   gcloud billing projects link [PROJECT_ID] --billing-account=[BILLING_ACCOUNT_ID]
   ```

3. **Run the Setup Script**: Execute the setup script which configures the entire deployment pipeline:

   ```bash
   chmod +x setup_cicd.sh
   ./setup_cicd.sh
   ```

   The script will prompt you for:

   - Email settings for notifications

   This script will:

   - Initialize Google Cloud resources (Cloud Run, Cloud SQL, Servie Accounts, etc.)
   - Set up GitHub Actions for CI/CD
   - Configure authentication and permissions
   - Create required database schemas
   - Deploy the initial version of MailMate backend

4. **Verify Deployment**: Once the script completes, you should have:
   - A running Email Assistant service on Cloud Run
   - A running MLflow server for experiment tracking
   - A bucket for MLflow
   - One database each for the Email Assistant and MLflow service
   - A CI/CD pipeline that automatically deploys changes

### OAuth Client ID setup

You will need to create an OAuth Client in GCP. To do this:

1. Go to GCP Console > APIs and Services > Credentials > Create Credentials > OAuth Client
2. Set application type as 'Web Application'
3. Set the name
4. Create
5. Copy the Client ID
6. Go to the Data Access Tab > 'Add or remove scopes'
7. Set the following scopes:
   - userinfo.email
   - gmail.send
   - gmail.readonly
8. Go to Audience Tab > 'Add users' under Test Users
9. Put in the Gmail address that you want to use with the extension.

**NOTE: We only need to do this since the extension is unpublished. Requires permission from Google to publish on the Chrome Web Store.**

### Secret Manager Setup

The `setup_cicd.sh` script will create three secrets in Secret Manager: `service-account-credentials`, `gmail-credentials`, `gmail-notification`

The secret values for these need to be populated as follows:

- `service-account-credentials`: Upload the `github-actions-sa-key.json` created by the script.
- `gmail-credentials`: Upload the JSON from the OAuth Client ID.
- `gmail-notification`: Same as above, but remove the 'installed' key. Also, you will need to add a new key called `refresh_token`. Its value can be set by following instructions in the [Data Pipeline README](/data_pipeline/README.md).

### GitHub Secret Variable Setup

If you want to run github yml files other than deploy.yml (which is enough if you want to just run model and don't test anything else), you will need to add the following in GitHub -> Your repository -> Setting -> Sectres & variables -> Actions

The secret values for these need to be populated as follows:

- `GCP_GMAIL_SA_KEY_JSON`: base64 endcoded `gmail-notification` value, set in Secret Manager Setup.
- `GCP_DVC_SA_KEY_JSON`: direct value of `service-account-credentials` set up in Secret Manager Setup.
- `NOTIFICATION_SENDER_EMAIL`: If not set up yet, it should be the one whose refresh token is added in `gmail-notification` step in Secret Manager Setup.
- `NOTIFICATION_RECIPIENT_EMAIL`: If not set up yet, add your desired valid recipient.

### Chrome Extension Setup

To install the Chrome extension for testing:

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top-right corner
3. Click "Load unpacked" and select the `extension` folder from this repository
4. Copy the extension ID shown
5. Replace the value in `REDIRECT_URI` in `config.js`.
   `REDIRECT_URI: "https://<extension_id>.chromiumapp.org"`

6. Copy the Email Assistant Cloud Run Function endpoint and replace it in `SERVER_URL` and `FEEDBACK_URL` in `config.js`.

   ```
   SERVER_URL: "https://<endpoint_url>/fetch_gmail_thread"

   FEEDBACK_URL: "https://<endpoint_url>/store_feedback"
   ```

7. Replace the value in `CLIENT_ID` in `config.js`.
   `CLIENT_ID: "<client_id>.apps.googleusercontent.com"`
8. Refresh the extension by clicking the reload icon on the extensions page in the browser.
9. The MailMate extension should now be installed and visible in your extensions list
10. Pin the extension to your toolbar for easy access
11. Open a Gmail thread and click the MailMate icon to use the assistant
12. Paste the REDIRECT_URI as an authorized redirect URI in your OAuth Client (follow the same steps to open the settings as before).

## Testing the Deployment

To verify your deployment:

1. **Health Check**: Visit `https://<your-service-url>/health` to ensure the service is running

2. **Test with Extension**: Use the Chrome extension with Gmail to test the full workflow:
   - Open Gmail and select an email
   - Click the MailMate icon
   - Select tasks (summary, action items, or draft reply)
   - Click "Analyze Email" to test the service
   - Authorize with your Google Account
   - View the outputs from the AI and provide feedback

## Video Demonstration

For a complete walkthrough of the deployment process and system functionality, please watch our demonstration video: [Video Link Here](https://drive.google.com/file/d/1Jr1CoPq95whpQ-tOgsVYKPlwb9RK5W4s/view?usp=sharing)

## Troubleshooting

If you encounter issues during deployment:

- **Authentication Errors**:

  - Check if your Google Cloud credentials are properly set up
  - Verify your service account has the necessary permissions
  - Run `gcloud auth application-default login` to refresh credentials
  - The GitHub Actions deployment might fail due to `gcloud auth`

    - Use the following commands to reset the secret in your GitHub account:

    ```
    gh secret delete GCP_SA_KEY --repo="your_username/email-assistant"

    cat github-actions-sa-key.json | gh secret set GCP_SA_KEY --repo="your_username/email-assistant"
    ```

- **'No Gmail Window Found' error in extension**:

  - If you see this type of error in the extension, refresh the Gmail page in your browser.

- **Failure in setup_cicd.sh due to not finding a valid Service Account**:

  - This is unlikely to happen, but it usually does when the newly created account is not made visible to the SDK. If this happens, you can simply re-run the script again.

- **Database Connection Issues**:

  - Verify that your Cloud SQL instance is running and accessible
  - Check if your IP is allowlisted in Cloud SQL settings
  - Test connection using `gcloud sql connect [INSTANCE_NAME] --user=postgres`

- **Extension Errors**:

  - Check the console logs in Chrome DevTools for detailed error messages
  - Make sure your `config.js` has the correct SERVER_URL
  - Verify the OAuth client ID matches between manifest.json and config.js

- **CSV FILES SETUP (IF GITHUB ACTIONS FAIL)**:

  Our CSV files are set up in dvc too, larger files are fetched up from there. You may need to adjust the `Data file paths` section in `model_pipeline/scripts/config.py` to use your csvs. In the project files mainly SAMPLE & SAMPLE FROM csv are used so adjust them accordingly. To run bias_checker.py you will need to make LABELED_SAMPLE_FROM_CSV_PATH which is just FROM column from enron_emails.csv merged with LABELED_SAMPLE_CSV_PATH. You will need to make this csv in the model_pipeline/data/ path or just replace it with appropriate one.

- **Deployment Script Issues**:

  - If `setup_cicd.sh` fails, check the output for specific error messages
  - Make sure you have the necessary permissions in your GCP project
  - Try running commands from the script individually to isolate issues

- **Logging**:

  - Check Cloud Logging for detailed error messages from the service
  - Filter logs by resource type (Cloud Run) and service name

- **MLflow Server Issues**:
  - Verify the MLflow server is running: `curl https://[MLFLOW-URL]/`
  - Check if the bucket for artifacts exists and is accessible

## Additional Scripts

The repository includes several utility scripts:

- `test_endpoints.py`: Tests all API endpoints for functionality
- `prompt_update_demo.py`: Demonstrates the prompt optimization system
- `populate_metrics.py`: Generates synthetic logs for dashboard testing
- `runmetricsdemo.sh`: Sets up and runs a metrics demonstration

## Contact

For questions or collaboration, please reach out to any of the team members listed at the top of this README or open an issue on this GitHub repository.
