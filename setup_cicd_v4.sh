#!/bin/bash
set -e

# Setup CI/CD Pipeline for MailMate Email Assistant with Cloud Run deployment
echo "==== Setting up CI/CD Pipeline for MailMate Email Assistant ===="
echo ""

# Check for required tools
command -v git >/dev/null 2>&1 || { echo "Error: git is required but not installed. Please install git first."; exit 1; }

# If GitHub CLI is available, check authentication
if command -v gh >/dev/null 2>&1; then
  if ! gh auth status >/dev/null 2>&1; then
    echo "GitHub CLI is not authenticated. Please authenticate now."
    gh auth login
  else
    echo "GitHub CLI is already authenticated."
  fi
fi

# Initialize and authenticate gcloud
echo ""
echo "=== Initializing Google Cloud SDK ==="

# Check if gcloud is initialized
if ! gcloud config get-value project >/dev/null 2>&1; then
  echo "gcloud needs to be initialized. Running gcloud init..."
  gcloud init --console-only
else
  echo "gcloud is already initialized."
fi

# Verify gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null 2>&1; then
  echo "You need to authenticate with Google Cloud."
  gcloud auth login
else
  echo "Already authenticated with Google Cloud."
fi

# Create GitHub secrets directory if not exists
mkdir -p .github/workflows

# Copy the GitHub Actions workflow file
if [ -f ".github/workflows/deploy.yml" ]; then
  echo "GitHub Actions workflow file already exists. Skipping..."
else
  echo "Creating GitHub Actions workflow file..."
  cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy MailMate Email Assistant

on:
  push:
    branches: [ main, master ]
    paths:
      - 'model_pipeline/**'
      - 'mlflow_server/**'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'model_pipeline/**'
      - 'mlflow_server/**'
  workflow_dispatch:  # Allow manual triggering

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  EMAIL_SERVICE_NAME: test-email-assistant
  MLFLOW_SERVICE_NAME: test-mlflow-server
  REGION: us-central1
  MIN_INSTANCES: 1
  MAX_INSTANCES: 2
  MEMORY: 2Gi
  CPU: 2
  TIMEOUT: 600s
  CONCURRENCY: 10
  DB_NAME: mail_mate_user_data
  DB_USER: ${{ secrets.DB_USER }}
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
  DB_HOST: ${{ secrets.DB_HOST }}
  DB_PORT: 5432
  GCP_LOCATION: us-central1
  GEMINI_MODEL: gemini-1.5-flash-002
  DB_SOCKET_DIR: /cloudsql
  EMAIL_DB_INSTANCE: test-emaildb
  MLFLOW_DB_INSTANCE: test-mlflow-db
  EMAIL_DB_CONNECTION_NAME: ${{ secrets.EMAIL_DB_CONNECTION_NAME }}
  MLFLOW_DB_CONNECTION_NAME: ${{ secrets.MLFLOW_DB_CONNECTION_NAME }}
  MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
  NOTIFICATION_SENDER_EMAIL: ${{ secrets.NOTIFICATION_SENDER_EMAIL }}
  NOTIFICATION_RECIPIENT_EMAIL: ${{ secrets.NOTIFICATION_RECIPIENT_EMAIL }}
  MLFLOW_EXPERIMENT_NAME: Test_MailMate_Email_Assistant
  FLASK_PORT: 8000
  GMAIL_API_SECRET_ID: gmail-credentials
  GMAIL_NOTIFICATION_SECRET_ID: gmail-notification
  SERVICE_ACCOUNT_SECRET_ID: service-account-credentials
  MLFLOW_BUCKET_NAME: test-mail-mate-mlflow-logs

jobs:
  build-and-deploy-mlflow:
    name: Build and Deploy MLflow Server
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
    
    - name: Set up Google Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        export_default_credentials: true
    
    - name: Enable required APIs
      run: |
        gcloud services enable cloudbuild.googleapis.com run.googleapis.com \
          artifactregistry.googleapis.com cloudresourcemanager.googleapis.com \
          secretmanager.googleapis.com logging.googleapis.com monitoring.googleapis.com \
          sqladmin.googleapis.com storage.googleapis.com

    - name: Create or verify Cloud Storage bucket for MLflow artifacts
      run: |
        if ! gsutil ls -b gs://$MLFLOW_BUCKET_NAME &>/dev/null; then
          echo "Creating bucket: $MLFLOW_BUCKET_NAME"
          gsutil mb -l $REGION gs://$MLFLOW_BUCKET_NAME
        else
          echo "Bucket $MLFLOW_BUCKET_NAME already exists"
        fi
        
        # Set Storage Object Admin permissions for service account
        SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="displayName:Cloud Run Service Agent" --format="value(email)")
        gsutil iam ch serviceAccount:$SERVICE_ACCOUNT:roles/storage.objectAdmin gs://$MLFLOW_BUCKET_NAME
    
    - name: Build and push MLflow Docker image
      id: build-mlflow
      run: |
        cd mlflow_server
        IMAGE_URL="us-central1-docker.pkg.dev/$PROJECT_ID/test-mlflow-repo/mlflow-server:latest"
        
        # Create Artifact Registry repository if it doesn't exist
        if ! gcloud artifacts repositories describe test-mlflow-repo --location=$REGION &>/dev/null; then
          gcloud artifacts repositories create test-mlflow-repo --repository-format=docker --location=$REGION
        fi
        
        gcloud builds submit --tag $IMAGE_URL . --timeout=30m
        echo "image=$IMAGE_URL" >> $GITHUB_OUTPUT
        
    - name: Create or verify Cloud SQL for MLflow
      run: |
        # Check if MLflow database instance exists
        if ! gcloud sql instances describe $MLFLOW_DB_INSTANCE &>/dev/null; then
          echo "Creating Cloud SQL instance for MLflow: $MLFLOW_DB_INSTANCE"
          gcloud sql instances create $MLFLOW_DB_INSTANCE \
            --database-version=POSTGRES_16 \
            --tier=db-custom-1-3840 \
            --region=$REGION \
            --root-password=${{ secrets.DB_PASSWORD }} \
            --storage-type=SSD \
            --storage-size=10GB \
            --availability-type=ZONAL \
            --no-backup
            
          # Create MLflow database
          echo "Creating MLflow database"
          gcloud sql databases create mlflow --instance=$MLFLOW_DB_INSTANCE
        else
          echo "MLflow Cloud SQL instance already exists: $MLFLOW_DB_INSTANCE"
        fi
    
    - name: Setup Service Account for MLflow Server
      run: |
        # Create service account for MLflow server if it doesn't exist
        MLFLOW_SA_NAME="test-mlflow-server"
        MLFLOW_SA_EMAIL="$MLFLOW_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
        
        if ! gcloud iam service-accounts describe $MLFLOW_SA_EMAIL &>/dev/null; then
          echo "Creating service account for MLflow server: $MLFLOW_SA_EMAIL"
          gcloud iam service-accounts create $MLFLOW_SA_NAME --display-name="MLflow Server Service Account"
          
          # Grant required roles
          gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$MLFLOW_SA_EMAIL" \
            --role="roles/cloudsql.client"
            
          gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$MLFLOW_SA_EMAIL" \
            --role="roles/storage.objectAdmin"
        else
          echo "MLflow service account already exists: $MLFLOW_SA_EMAIL"
        fi
        
        # Store the service account email for Cloud Run deployment
        echo "mlflow_sa=$MLFLOW_SA_EMAIL" >> $GITHUB_OUTPUT
    
    - name: Deploy MLflow Server to Cloud Run
      run: |
        MLFLOW_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${MLFLOW_DB_INSTANCE}"
        MLFLOW_SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:MLflow Server Service Account" --format="value(email)")
        
        if [[ -z "$MLFLOW_SA_EMAIL" ]]; then
          MLFLOW_SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:Cloud Run Service Agent" --format="value(email)")
        fi
        
        # Create volume for MLflow artifacts bucket
        echo "Creating volume for MLflow artifacts bucket..."
        gcloud run services update $MLFLOW_SERVICE_NAME \
          --add-volume=name=mlflow_bucket,type=cloud-storage,bucket=$MLFLOW_BUCKET_NAME \
          --region $REGION \
          --update-env-vars="" \
          2>/dev/null || echo "Creating service with volume..."
        
        # Deploy MLflow server to Cloud Run
        gcloud run deploy $MLFLOW_SERVICE_NAME \
          --image ${{ steps.build-mlflow.outputs.image }} \
          --platform managed \
          --region $REGION \
          --service-account $MLFLOW_SA_EMAIL \
          --allow-unauthenticated \
          --min-instances 0 \
          --max-instances 1 \
          --memory 512Mi \
          --cpu 1 \
          --port 5000 \
          --set-env-vars "MLFLOW_BACKEND_STORE_URI=postgresql+psycopg2://$DB_USER:$DB_PASSWORD@/mlflow?host=/cloudsql/$MLFLOW_CONNECTION_NAME,MLFLOW_DEFAULT_ARTIFACT_ROOT=gs://$MLFLOW_BUCKET_NAME/mlflow-artifacts" \
          --add-cloudsql-instances $MLFLOW_CONNECTION_NAME \
          --add-volume=name=mlflow_bucket,type=cloud-storage,bucket=$MLFLOW_BUCKET_NAME \
          --add-volume-mount=volume=mlflow_bucket,mount-path=/mnt/gcs \
          --timeout 300s
          
        # Get the MLflow service URL and save it for the email assistant deployment
        MLFLOW_URL=$(gcloud run services describe $MLFLOW_SERVICE_NAME --region $REGION --format="value(status.url)")
        echo "MLFLOW_TRACKING_URI=$MLFLOW_URL" >> $GITHUB_ENV
        
        echo "MLflow server deployed successfully at: $MLFLOW_URL"
        # Store the MLflow URL as a GitHub output
        echo "mlflow_url=$MLFLOW_URL" >> $GITHUB_OUTPUT

  build-and-deploy-email:
    name: Build and Deploy Email Assistant
    needs: build-and-deploy-mlflow
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
    
    - name: Set up Google Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        export_default_credentials: true
    
    - name: Enable required APIs
      run: |
        gcloud services enable cloudbuild.googleapis.com run.googleapis.com \
          artifactregistry.googleapis.com cloudresourcemanager.googleapis.com \
          secretmanager.googleapis.com logging.googleapis.com monitoring.googleapis.com \
          sqladmin.googleapis.com
    
    - name: Create or verify Cloud SQL for Email Assistant
      run: |
        # Check if Email database instance exists
        if ! gcloud sql instances describe $EMAIL_DB_INSTANCE &>/dev/null; then
          echo "Creating Cloud SQL instance for Email Assistant: $EMAIL_DB_INSTANCE"
          gcloud sql instances create $EMAIL_DB_INSTANCE \
            --database-version=POSTGRES_16 \
            --tier=db-custom-1-3840 \
            --region=$REGION \
            --root-password=${{ secrets.DB_PASSWORD }} \
            --storage-type=SSD \
            --storage-size=10GB \
            --availability-type=ZONAL \
            --no-backup
            
          # Create email database
          echo "Creating mail_mate_user_data database"
          gcloud sql databases create $DB_NAME --instance=$EMAIL_DB_INSTANCE
        else
          echo "Email Cloud SQL instance already exists: $EMAIL_DB_INSTANCE"
        fi
    
    - name: Build and push Docker image
      id: build
      run: |
        cd model_pipeline
        IMAGE_URL="gcr.io/$PROJECT_ID/$EMAIL_SERVICE_NAME:$(date +%Y%m%d-%H%M%S)"
        gcloud builds submit --tag $IMAGE_URL . --timeout=30m
        echo "image=$IMAGE_URL" >> $GITHUB_OUTPUT
    
    - name: Grant service account access to Cloud SQL
      run: |
        # Get the Cloud Run service account email
        SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="displayName:Cloud Run Service Agent" --format="value(email)")
        
        # Grant the Cloud SQL Client role
        gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:$SERVICE_ACCOUNT" \
          --role="roles/cloudsql.client"
      
        # Get the MLflow URL from the previous job
        MLFLOW_URL="${{ needs.build-and-deploy-mlflow.outputs.mlflow_url }}"
        EMAIL_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${EMAIL_DB_INSTANCE}"
    
    - name: Deploy to Cloud Run
      run: |
        # Get the MLflow URL from the previous job
        MLFLOW_URL="${{ needs.build-and-deploy-mlflow.outputs.mlflow_url }}"
        EMAIL_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${EMAIL_DB_INSTANCE}"
        
        gcloud run deploy $EMAIL_SERVICE_NAME \
          --image ${{ steps.build.outputs.image }} \
          --platform managed \
          --region $REGION \
          --allow-unauthenticated \
          --min-instances $MIN_INSTANCES \
          --max-instances $MAX_INSTANCES \
          --memory $MEMORY \
          --cpu $CPU \
          --timeout $TIMEOUT \
          --concurrency $CONCURRENCY \
          --set-env-vars "DB_NAME=$DB_NAME,DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD,DB_HOST=$DB_HOST,DB_PORT=$DB_PORT,GCP_LOCATION=$GCP_LOCATION,GEMINI_MODEL=$GEMINI_MODEL,DB_SOCKET_DIR=$DB_SOCKET_DIR,INSTANCE_CONNECTION_NAME=$EMAIL_CONNECTION_NAME,MLFLOW_TRACKING_URI=$MLFLOW_URL,NOTIFICATION_SENDER_EMAIL=$NOTIFICATION_SENDER_EMAIL,NOTIFICATION_RECIPIENT_EMAIL=$NOTIFICATION_RECIPIENT_EMAIL,MLFLOW_EXPERIMENT_NAME=$MLFLOW_EXPERIMENT_NAME,FLASK_PORT=$FLASK_PORT,GMAIL_API_SECRET_ID=$GMAIL_API_SECRET_ID,GMAIL_NOTIFICATION_SECRET_ID=$GMAIL_NOTIFICATION_SECRET_ID,SERVICE_ACCOUNT_SECRET_ID=$SERVICE_ACCOUNT_SECRET_ID" \
          --add-cloudsql-instances=$EMAIL_CONNECTION_NAME \
          --command="python" \
          --args="scripts/fetch_gmail_threads.py"
    
    - name: Get Service URL
      run: |
        SERVICE_URL=$(gcloud run services describe $EMAIL_SERVICE_NAME --region $REGION --format 'value(status.url)')
        echo "::notice::Deployment successful! Service URL: $SERVICE_URL"

  setup-monitoring:
    name: Setup Monitoring and Scheduler
    needs: build-and-deploy-email
    if: github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
    
    - name: Set up Google Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        export_default_credentials: true
    
    - name: Set up Cloud Scheduler
      run: |
        cd model_pipeline/scripts
        bash setup_cloud_scheduler.sh
    
    - name: Set up Cloud Monitoring
      run: |
        cd model_pipeline/scripts
        bash setup_cloud_monitoring.sh
        bash make_dash2.sh
EOF
  echo "GitHub Actions workflow file created successfully."
fi

# Prompt for GCP project configuration
echo ""
echo "==== Google Cloud Platform Configuration ===="
# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
read -p "Enter your GCP Project ID [$CURRENT_PROJECT]: " GCP_PROJECT_ID
GCP_PROJECT_ID=${GCP_PROJECT_ID:-$CURRENT_PROJECT}

# Set the project in gcloud config
gcloud config set project ${GCP_PROJECT_ID}

read -p "Enter the desired GCP region (default: us-central1): " GCP_REGION
GCP_REGION=${GCP_REGION:-us-central1}

# Enable required APIs
echo ""
echo "=== Enabling Required Google Cloud APIs ==="
echo "This may take a few minutes..."

gcloud services enable cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudresourcemanager.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudscheduler.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com

# Create service account for GitHub Actions
echo ""
echo "==== Creating Service Account for GitHub Actions ===="
SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account already exists
if gcloud iam service-accounts describe ${SA_EMAIL} >/dev/null 2>&1; then
  echo "Service account ${SA_EMAIL} already exists."
else
  echo "Creating service account ${SA_EMAIL}..."
  gcloud iam service-accounts create ${SA_NAME} \
    --display-name="GitHub Actions Deployer"
fi

# Grant necessary permissions to the service account
echo "Granting necessary permissions to the service account..."
roles=(
  "roles/run.admin"
  "roles/cloudbuild.builds.builder"
  "roles/storage.admin"
  "roles/iam.serviceAccountUser"
  "roles/secretmanager.secretAccessor"
  "roles/monitoring.admin"
  "roles/cloudscheduler.admin"
  "roles/cloudsql.admin"
  "roles/artifactregistry.admin"
  "roles/serviceusage.serviceUsageAdmin"
)

for role in "${roles[@]}"; do
  gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${role}"
done

# Create and download service account key
echo "Creating service account key..."
KEY_FILE="github-actions-sa-key.json"
if [ -f ${KEY_FILE} ]; then
  echo "Service account key already exists. Skipping key creation."
else
  gcloud iam service-accounts keys create ${KEY_FILE} \
    --iam-account=${SA_EMAIL}
  echo "Service account key created and saved to ${KEY_FILE}"
  echo "IMPORTANT: Keep this key secure and do not commit it to version control."
fi

# Set up Cloud SQL Database for Email Assistant
echo ""
echo "==== Email Assistant Database Setup ===="
echo "Do you want to set up a Cloud SQL PostgreSQL database for Email Assistant? (y/n)"
read setup_email_database

EMAIL_DB_INSTANCE_NAME="test-emaildb"
EMAIL_DB_CONNECTION_NAME="${GCP_PROJECT_ID}:${GCP_REGION}:${EMAIL_DB_INSTANCE_NAME}"

if [[ "$setup_email_database" == "y" ]]; then
  echo "Setting up Cloud SQL PostgreSQL instance: ${EMAIL_DB_INSTANCE_NAME}"
  
  # Check if database instance already exists
  if gcloud sql instances describe ${EMAIL_DB_INSTANCE_NAME} --project=${GCP_PROJECT_ID} >/dev/null 2>&1; then
    echo "Database instance ${EMAIL_DB_INSTANCE_NAME} already exists. Skipping database creation."
    
    # Even if the instance exists, prompt for DB credentials for GitHub secrets
    read -p "Enter database username [postgres]: " DB_USER
    DB_USER=${DB_USER:-postgres}
    read -sp "Enter database password: " DB_PASSWORD
    echo ""
    
    echo "Using existing database instance: ${EMAIL_DB_INSTANCE_NAME}"
    echo "Instance Connection Name: ${EMAIL_DB_CONNECTION_NAME}"
  else
    echo "Creating database instance ${EMAIL_DB_INSTANCE_NAME} with configuration matching existing setup..."
    gcloud sql instances create ${EMAIL_DB_INSTANCE_NAME} \
      --database-version=POSTGRES_16 \
      --tier=db-custom-1-3840 \
      --region=${GCP_REGION} \
      --root-password="postgres" \
      --storage-type=SSD \
      --storage-size=10GB \
      --availability-type=ZONAL \
      --no-backup \
      --assign-ip
    
    # Create database
    echo "Creating database: mail_mate_user_data"
    gcloud sql databases create mail_mate_user_data \
      --instance=${EMAIL_DB_INSTANCE_NAME}
    
    # Create user
    DB_USER="postgres"
    echo "Enter database password for user ${DB_USER}:"
    read -sp "Password: " DB_PASSWORD
    echo ""
    
    gcloud sql users create ${DB_USER} \
      --instance=${EMAIL_DB_INSTANCE_NAME} \
      --password="${DB_PASSWORD}"
    
    # Execute the SQL file using gcloud sql import
    echo "Importing SQL file to create tables..."
    gcloud sql import sql ${EMAIL_DB_INSTANCE_NAME} ./create_tables.sql \
      --database=mail_mate_user_data \
      --quiet 
      
    echo "Email Assistant Cloud SQL Database setup complete!"
    echo "Instance Connection Name: ${EMAIL_DB_CONNECTION_NAME}"
  fi
else
  echo "Skipping email database setup. You'll need to provide database credentials manually."
  read -p "Database host: " DB_HOST
  read -p "Database username: " DB_USER
  read -sp "Database password: " DB_PASSWORD
  echo ""
  
  # Setup environment variables
  DB_HOST=${DB_HOST:-cloudsql}
  DB_USER=${DB_USER:-postgres}
fi

# Set up MLflow Database
echo ""
echo "==== MLflow Database Setup ===="
echo "Do you want to set up a Cloud SQL PostgreSQL database for MLflow? (y/n)"
read setup_mlflow_database

MLFLOW_DB_INSTANCE_NAME="test-mlflow-db"
MLFLOW_DB_CONNECTION_NAME="${GCP_PROJECT_ID}:${GCP_REGION}:${MLFLOW_DB_INSTANCE_NAME}"

if [[ "$setup_mlflow_database" == "y" ]]; then
  echo "Setting up Cloud SQL PostgreSQL instance: ${MLFLOW_DB_INSTANCE_NAME}"
  
  if gcloud sql instances describe ${MLFLOW_DB_INSTANCE_NAME} --project=${GCP_PROJECT_ID} >/dev/null 2>&1; then
    echo "MLflow database instance ${MLFLOW_DB_INSTANCE_NAME} already exists. Skipping database creation."
  else
    echo "Creating MLflow database instance ${MLFLOW_DB_INSTANCE_NAME}..."
    gcloud sql instances create ${MLFLOW_DB_INSTANCE_NAME} \
      --database-version=POSTGRES_16 \
      --tier=db-custom-1-3840 \
      --region=${GCP_REGION} \
      --root-password="${DB_PASSWORD}" \
      --storage-type=SSD \
      --storage-size=10GB \
      --availability-type=ZONAL \
      --no-backup \
      --assign-ip
    
    # Create database
    echo "Creating database: mlflow"
    gcloud sql databases create mlflow \
      --instance=${MLFLOW_DB_INSTANCE_NAME}
    
    # Create user (using same credentials as email database for simplicity)
    gcloud sql users create ${DB_USER} \
      --instance=${MLFLOW_DB_INSTANCE_NAME} \
      --password="${DB_PASSWORD}"
      
    echo "MLflow Cloud SQL Database setup complete!"
    echo "Instance Connection Name: ${MLFLOW_DB_CONNECTION_NAME}"
  fi
fi

# Create GCS bucket for MLflow artifacts
echo ""
echo "==== MLflow Storage Bucket Setup ===="
echo "Do you want to create a Cloud Storage bucket for MLflow artifacts? (y/n)"
read create_mlflow_bucket

MLFLOW_BUCKET_NAME="test-mail-mate-mlflow-logs"

if [[ "$create_mlflow_bucket" == "y" ]]; then
  if gsutil ls -b gs://${MLFLOW_BUCKET_NAME} >/dev/null 2>&1; then
    echo "MLflow bucket ${MLFLOW_BUCKET_NAME} already exists."
  else
    echo "Creating Cloud Storage bucket: ${MLFLOW_BUCKET_NAME}"
    gsutil mb -l ${GCP_REGION} gs://${MLFLOW_BUCKET_NAME}
    
    echo "MLflow storage bucket created successfully!"
  fi
fi

# Create service account for MLflow Server
echo ""
echo "==== Creating Service Account for MLflow Server ===="
MLFLOW_SA_NAME="test-mlflow-server"
MLFLOW_SA_EMAIL="${MLFLOW_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe ${MLFLOW_SA_EMAIL} >/dev/null 2>&1; then
  echo "MLflow service account ${MLFLOW_SA_EMAIL} already exists."
else
  echo "Creating service account ${MLFLOW_SA_EMAIL}..."
  gcloud iam service-accounts create ${MLFLOW_SA_NAME} \
    --display-name="MLflow Server Service Account"
fi

# Grant necessary permissions to the MLflow service account
echo "Granting necessary permissions to the MLflow service account..."
mlflow_roles=(
  "roles/cloudsql.client"
  "roles/storage.objectAdmin"
)

for role in "${mlflow_roles[@]}"; do
  gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
    --member="serviceAccount:${MLFLOW_SA_EMAIL}" \
    --role="${role}"
done

# Set up MLflow tracking and notification emails
echo ""
echo "==== Additional Configuration ===="
read -p "Enter notification sender email [shubhdesai111@gmail.com]: " NOTIFICATION_SENDER_EMAIL
NOTIFICATION_SENDER_EMAIL=${NOTIFICATION_SENDER_EMAIL:-shubhdesai111@gmail.com}
read -p "Enter notification recipient email [shubhdesai4@gmail.com]: " NOTIFICATION_RECIPIENT_EMAIL
NOTIFICATION_RECIPIENT_EMAIL=${NOTIFICATION_RECIPIENT_EMAIL:-shubhdesai4@gmail.com}

# Create Artifact Registry repository for MLflow
echo ""
echo "==== Creating Artifact Registry for MLflow Server ===="
if gcloud artifacts repositories describe test-mlflow-repo --location=${GCP_REGION} >/dev/null 2>&1; then
  echo "Artifact Registry repository 'test-mlflow-repo' already exists."
else
  echo "Creating Artifact Registry repository: test-mlflow-repo"
  gcloud artifacts repositories create test-mlflow-repo \
    --repository-format=docker \
    --location=${GCP_REGION}
  echo "Artifact Registry repository created successfully!"
fi

# Deploy MLflow Server to Cloud Run
echo ""
echo "==== MLflow Server Deployment ===="
echo "Do you want to deploy the MLflow server to Cloud Run? (y/n)"
read deploy_mlflow_server

if [[ "$deploy_mlflow_server" == "y" ]]; then
  # Navigate to the mlflow_server directory
  cd "$(dirname "$0")"  # Go to directory of script
  cd ../mlflow_server || cd mlflow_server  # Try to enter mlflow_server directory
  
  # Build and push the MLflow Docker image
  echo "Building and pushing MLflow Docker image..."
  MLFLOW_SERVICE_NAME="test-mlflow-server"
  MLFLOW_IMAGE_URL="us-central1-docker.pkg.dev/${GCP_PROJECT_ID}/test-mlflow-repo/mlflow-server:latest"
  
  if [ -f "Dockerfile" ]; then
    gcloud builds submit --tag ${MLFLOW_IMAGE_URL} . --timeout=30m
    
    # Deploy MLflow to Cloud Run
    echo "Deploying MLflow server to Cloud Run..."
    gcloud run deploy ${MLFLOW_SERVICE_NAME} \
      --image ${MLFLOW_IMAGE_URL} \
      --platform managed \
      --region ${GCP_REGION} \
      --service-account ${MLFLOW_SA_EMAIL} \
      --allow-unauthenticated \
      --min-instances 0 \
      --max-instances 1 \
      --memory 512Mi \
      --cpu 1 \
      --port 5000 \
      --set-env-vars "MLFLOW_BACKEND_STORE_URI=postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@/mlflow?host=/cloudsql/${MLFLOW_DB_CONNECTION_NAME},MLFLOW_DEFAULT_ARTIFACT_ROOT=gs://${MLFLOW_BUCKET_NAME}/mlflow-artifacts" \
      --add-cloudsql-instances ${MLFLOW_DB_CONNECTION_NAME} \
      --add-volume=name=mlflow_bucket,type=cloud-storage,bucket=${MLFLOW_BUCKET_NAME} \
      --add-volume-mount=volume=mlflow_bucket,mount-path=/mnt/gcs \
      --timeout 300s
      
    # Get the MLflow service URL
    MLFLOW_URL=$(gcloud run services describe ${MLFLOW_SERVICE_NAME} --region ${GCP_REGION} --format="value(status.url)")
    echo "✅ MLflow server deployed successfully! MLflow URL: ${MLFLOW_URL}"
    
    # Save MLflow URL for email assistant deployment
    MLFLOW_TRACKING_URI=${MLFLOW_URL}
  else
    echo "MLflow Dockerfile not found. Please make sure mlflow_server/Dockerfile exists."
    MLFLOW_TRACKING_URI="https://test-mlflow-server-673808915782.us-central1.run.app"
    echo "Using default MLflow tracking URI: ${MLFLOW_TRACKING_URI}"
  fi
fi

# Create Cloud Run service and deploy Email Assistant
echo ""
echo "==== Email Assistant Deployment ===="
echo "Do you want to deploy the Email Assistant to Cloud Run? (y/n)"
read deploy_email_assistant

if [[ "$deploy_email_assistant" == "y" ]]; then
  # Navigate to the model_pipeline directory
  cd "$(dirname "$0")"  # Go to directory of script
  cd ../model_pipeline || cd model_pipeline  # Try to enter model_pipeline directory
  
  # Build and push the Docker image
  echo "Building and pushing Email Assistant Docker image..."
  EMAIL_SERVICE_NAME="test-email-assistant"
  EMAIL_IMAGE_URL="gcr.io/${GCP_PROJECT_ID}/${EMAIL_SERVICE_NAME}:$(date +%Y%m%d-%H%M%S)"
  gcloud builds submit --tag ${EMAIL_IMAGE_URL} . --timeout=30m
  
  # Setup Cloud SQL connection for Cloud Run
  echo "Setting up Cloud SQL connection for Cloud Run..."
  
  # Get the Cloud Run service account
  SERVICE_ACCOUNT="$(gcloud iam service-accounts list --filter="email ~ ^service-[0-9]+@gcp-sa-run.iam.gserviceaccount.com$" --format="value(email)")"
  
  if [[ -z "$SERVICE_ACCOUNT" ]]; then
    echo "Could not find Cloud Run service account. Using default compute service account."
    SERVICE_ACCOUNT="$(gcloud iam service-accounts list --filter="email ~ ^[0-9]+-compute@developer.gserviceaccount.com$" --format="value(email)")"
  fi
  
  # Grant Cloud SQL Client role to service account
  echo "Granting Cloud SQL Client role to ${SERVICE_ACCOUNT}..."
  gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/cloudsql.client"
  
  # Deploy to Cloud Run
  echo "Deploying Email Assistant to Cloud Run..."
  gcloud run deploy ${EMAIL_SERVICE_NAME} \
    --image ${EMAIL_IMAGE_URL} \
    --platform managed \
    --region ${GCP_REGION} \
    --allow-unauthenticated \
    --min-instances 1 \
    --max-instances 2 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600s \
    --concurrency 10 \
    --set-env-vars "DB_NAME=mail_mate_user_data,DB_USER=${DB_USER},DB_PASSWORD=${DB_PASSWORD},DB_HOST=${DB_HOST:-cloudsql},DB_PORT=5432,GCP_LOCATION=${GCP_REGION},GEMINI_MODEL=gemini-1.5-flash-002,DB_SOCKET_DIR=/cloudsql,INSTANCE_CONNECTION_NAME=${EMAIL_DB_CONNECTION_NAME},MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI},NOTIFICATION_SENDER_EMAIL=${NOTIFICATION_SENDER_EMAIL},NOTIFICATION_RECIPIENT_EMAIL=${NOTIFICATION_RECIPIENT_EMAIL},MLFLOW_EXPERIMENT_NAME=Test_MailMate_Email_Assistant" \
    --add-cloudsql-instances=${EMAIL_DB_CONNECTION_NAME} \
    --command="python" \
    --args="scripts/fetch_gmail_threads.py"
  
  # Get the URL of the deployed service
  EMAIL_SERVICE_URL=$(gcloud run services describe ${EMAIL_SERVICE_NAME} --region ${GCP_REGION} --format 'value(status.url)')
  echo "✅ Email Assistant deployment successful! Service URL: ${EMAIL_SERVICE_URL}"
  
  # Setup secrets for the service
  echo "Creating secrets in Secret Manager..."
  
  # Create secrets for API credentials if they don't exist
  for SECRET_ID in "gmail-credentials" "gmail-notification" "service-account-credentials"; do
    if ! gcloud secrets describe ${SECRET_ID} >/dev/null 2>&1; then
      echo "Creating secret: ${SECRET_ID}"
      gcloud secrets create ${SECRET_ID} --replication-policy="automatic"
      # Note: The actual secret values should be populated separately
      echo "Note: You'll need to populate the '${SECRET_ID}' secret separately via Google Cloud Console."
    else
      echo "Secret ${SECRET_ID} already exists."
    fi
  done
  
  # Grant the Cloud Run service account access to the secrets
  for SECRET_ID in "gmail-credentials" "gmail-notification" "service-account-credentials"; do
    echo "Granting access to ${SECRET_ID} for Cloud Run service account..."
    gcloud secrets add-iam-policy-binding ${SECRET_ID} \
      --member="serviceAccount:${SERVICE_ACCOUNT}" \
      --role="roles/secretmanager.secretAccessor"
  done
  
#   # Set up Cloud Scheduler for performance monitoring
#   echo "Setting up Cloud Scheduler for performance monitoring..."
#   cd scripts || cd ../scripts
#   bash setup_cloud_scheduler.sh
  
#   # Set up Cloud Monitoring
#   echo "Setting up Cloud Monitoring..."
#   bash setup_cloud_monitoring.sh
#   bash make_dash2.sh
  
  echo "Email Assistant setup complete!"
fi

# Check for GitHub CLI and set up secrets
if command -v gh >/dev/null 2>&1; then
  echo ""
  echo "==== Setting up GitHub Secrets ===="
  
  # Check if we're in a GitHub repository and GitHub CLI is authenticated
  if gh auth status >/dev/null 2>&1; then
    # Get the GitHub repository from remote
    GITHUB_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
    
    if [[ "$GITHUB_REMOTE" == *"github.com"* ]]; then
      # Extract owner and repo from remote URL, properly removing the .git extension
      GITHUB_REPO=$(echo $GITHUB_REMOTE | sed -E 's|.*github\.com[/:]([^/]+)/([^/]+)(\.git)?|\1/\2|' | sed 's/\.git$//')
      echo $GITHUB_REPO
      
      if [[ -n "$GITHUB_REPO" ]]; then
        echo "Setting up GitHub secrets for repository: $GITHUB_REPO"
        
        # Set up GitHub secrets with explicit repository
        echo "Setting GCP_PROJECT_ID secret..."
        echo ${GCP_PROJECT_ID} | gh secret set GCP_PROJECT_ID --repo="$GITHUB_REPO"
        
        echo "Setting GCP_SA_KEY secret (from ${KEY_FILE})..."
        cat ${KEY_FILE} | gh secret set GCP_SA_KEY --repo="$GITHUB_REPO"
        
        echo "Setting DB_USER secret..."
        echo ${DB_USER} | gh secret set DB_USER --repo="$GITHUB_REPO"
        
        echo "Setting DB_PASSWORD secret..."
        echo ${DB_PASSWORD} | gh secret set DB_PASSWORD --repo="$GITHUB_REPO"
        
        echo "Setting DB_HOST secret..."
        echo ${DB_HOST:-cloudsql} | gh secret set DB_HOST --repo="$GITHUB_REPO"
        
        # Set up connection names for both databases
        echo "Setting EMAIL_DB_CONNECTION_NAME secret..."
        echo ${EMAIL_DB_CONNECTION_NAME} | gh secret set EMAIL_DB_CONNECTION_NAME --repo="$GITHUB_REPO"
        
        echo "Setting MLFLOW_DB_CONNECTION_NAME secret..."
        echo ${MLFLOW_DB_CONNECTION_NAME} | gh secret set MLFLOW_DB_CONNECTION_NAME --repo="$GITHUB_REPO"
        
        echo "Setting MLFLOW_TRACKING_URI secret..."
        echo ${MLFLOW_TRACKING_URI} | gh secret set MLFLOW_TRACKING_URI --repo="$GITHUB_REPO"
        
        echo "Setting NOTIFICATION_SENDER_EMAIL secret..."
        echo ${NOTIFICATION_SENDER_EMAIL} | gh secret set NOTIFICATION_SENDER_EMAIL --repo="$GITHUB_REPO"
        
        echo "Setting NOTIFICATION_RECIPIENT_EMAIL secret..."
        echo ${NOTIFICATION_RECIPIENT_EMAIL} | gh secret set NOTIFICATION_RECIPIENT_EMAIL --repo="$GITHUB_REPO"
        
        echo "GitHub secrets set up successfully."
      else
        echo "Unable to determine GitHub repository from remote URL."
        echo "Please set up the following secrets manually in your GitHub repository:"
        echo "- GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
        echo "- GCP_SA_KEY: Contents of ${KEY_FILE}"
        echo "- DB_USER: ${DB_USER}"
        echo "- DB_PASSWORD: Your database password"
        echo "- DB_HOST: ${DB_HOST:-cloudsql}"
        echo "- EMAIL_DB_CONNECTION_NAME: ${EMAIL_DB_CONNECTION_NAME}"
        echo "- MLFLOW_DB_CONNECTION_NAME: ${MLFLOW_DB_CONNECTION_NAME}"
        echo "- MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI}"
        echo "- NOTIFICATION_SENDER_EMAIL: ${NOTIFICATION_SENDER_EMAIL}"
        echo "- NOTIFICATION_RECIPIENT_EMAIL: ${NOTIFICATION_RECIPIENT_EMAIL}"
      fi
    else
      echo "GitHub repository not detected in remote 'origin'."
      echo "Please set up the following secrets manually in your GitHub repository:"
      echo "- GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
      echo "- GCP_SA_KEY: Contents of ${KEY_FILE}"
      echo "- DB_USER: ${DB_USER}"
      echo "- DB_PASSWORD: Your database password"
      echo "- DB_HOST: ${DB_HOST:-cloudsql}"
      echo "- EMAIL_DB_CONNECTION_NAME: ${EMAIL_DB_CONNECTION_NAME}"
      echo "- MLFLOW_DB_CONNECTION_NAME: ${MLFLOW_DB_CONNECTION_NAME}"
      echo "- MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI}"
      echo "- NOTIFICATION_SENDER_EMAIL: ${NOTIFICATION_SENDER_EMAIL}"
      echo "- NOTIFICATION_RECIPIENT_EMAIL: ${NOTIFICATION_RECIPIENT_EMAIL}"
    fi
  else
    echo "GitHub CLI is not authenticated."
    echo "Please set up the following secrets manually in your GitHub repository:"
    echo "- GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
    echo "- GCP_SA_KEY: Contents of ${KEY_FILE}"
    echo "- DB_USER: ${DB_USER}"
    echo "- DB_PASSWORD: Your database password"
    echo "- DB_HOST: ${DB_HOST:-cloudsql}"
    echo "- EMAIL_DB_CONNECTION_NAME: ${EMAIL_DB_CONNECTION_NAME}"
    echo "- MLFLOW_DB_CONNECTION_NAME: ${MLFLOW_DB_CONNECTION_NAME}"
    echo "- MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI}"
    echo "- NOTIFICATION_SENDER_EMAIL: ${NOTIFICATION_SENDER_EMAIL}"
    echo "- NOTIFICATION_RECIPIENT_EMAIL: ${NOTIFICATION_RECIPIENT_EMAIL}"
  fi
else
  echo ""
  echo "GitHub CLI not installed. Please set up the following secrets manually in your GitHub repository:"
  echo "- GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
  echo "- GCP_SA_KEY: Contents of ${KEY_FILE}"
  echo "- DB_USER: ${DB_USER}"
  echo "- DB_PASSWORD: Your database password"
  echo "- DB_HOST: ${DB_HOST:-cloudsql}"
  echo "- EMAIL_DB_CONNECTION_NAME: ${EMAIL_DB_CONNECTION_NAME}"
  echo "- MLFLOW_DB_CONNECTION_NAME: ${MLFLOW_DB_CONNECTION_NAME}"
  echo "- MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI}"
  echo "- NOTIFICATION_SENDER_EMAIL: ${NOTIFICATION_SENDER_EMAIL}"
  echo "- NOTIFICATION_RECIPIENT_EMAIL: ${NOTIFICATION_RECIPIENT_EMAIL}"
fi

# Give instructions on completing setup
echo ""
echo "==== Setup Complete ===="
echo "CI/CD pipeline setup is complete. Follow these steps to finalize:"
echo ""
echo "1. Commit and push the GitHub Actions workflow file:"
echo "   git add .github/workflows/deploy.yml"
echo "   git commit -m 'Add GitHub Actions workflow for CI/CD'"
echo "   git push"
echo ""
echo "2. Ensure your repository has the required secrets:"
echo "   - GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
echo "   - GCP_SA_KEY: The content of the service account key file (${KEY_FILE})"
echo "   - DB_USER: ${DB_USER}"
echo "   - DB_PASSWORD: Your database password"
echo "   - DB_HOST: ${DB_HOST:-cloudsql}"
echo "   - EMAIL_DB_CONNECTION_NAME: ${EMAIL_DB_CONNECTION_NAME}"
echo "   - MLFLOW_DB_CONNECTION_NAME: ${MLFLOW_DB_CONNECTION_NAME}"
echo "   - MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI}"
echo "   - NOTIFICATION_SENDER_EMAIL: ${NOTIFICATION_SENDER_EMAIL}"
echo "   - NOTIFICATION_RECIPIENT_EMAIL: ${NOTIFICATION_RECIPIENT_EMAIL}"
echo ""
echo "3. You can trigger a deployment manually from the GitHub Actions tab"
echo "   in your repository. Look for the 'Deploy MailMate Email Assistant' workflow"
echo "   and click 'Run workflow'."
echo ""
echo "4. For additional configuration options, refer to the deployment guide."
echo ""
echo "CI/CD pipeline is now connected to your repository!"