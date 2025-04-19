"""
Module for handling data anomalies and sending notifications.

This module includes:
- `send_email_notification`: Sends email alerts using OAuth2 authentication.
- `handle_anomalies`: Logs detected anomalies and sends alerts if necessary.

Usage:
    Call `handle_anomalies` after validation to log and notify anomalies.

Functions:
    send_email_notification(subject, body, to_email, oauth_config, logger):
        Sends an email alert about detected anomalies.

    handle_anomalies(validation_results, log_path, logger_name):
        Logs anomalies and triggers email alerts when required.

"""

import os
import sys
import base64
from email.mime.text import MIMEText
import pandas as pd
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Add scripts folder to sys.path
scripts_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
sys.path.append(scripts_folder)

# pylint: disable=wrong-import-position
from create_logger import create_logger

dotenv_path = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=dotenv_path)


# pylint: disable=logging-fstring-interpolation
def send_email_notification(subject, body, to_email, oauth_config, logger):
    """Send an email notification using Gmail API with OAuth2 authentication.

    Args:
        subject (str): Email subject.
        body (str): Email body content.
        to_email (str): Recipient email address.
        oauth_config (dict): OAuth2 configuration with client_id, client_secret,
        refresh_token, sender_email.
        logger (logging.Logger): Logger instance for logging.

    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    try:
        creds = Credentials(
            token=None,
            refresh_token=oauth_config["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )
        if not creds.valid or creds.token is None:
            logger.info("Refreshing OAuth2 token...")
            creds.refresh(Request())

        # Create Gmail API service
        service = build("gmail", "v1", credentials=creds)

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = oauth_config["sender_email"]
        msg["To"] = to_email

        # Encode the message as base64 URL-safe string
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        message = {"raw": raw}

        # Send the email
        # pylint: disable=no-member
        service.users().messages().send(userId="me", body=message).execute()
        logger.info("Email notification sent successfully to %s", to_email)
        return True
    except HttpError as e:
        logger.error("Failed to send email via Gmail API: %s", e, exc_info=True)
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error sending email: %s", e, exc_info=True)
        return False


# pylint: disable=too-many-locals
def handle_anomalies(log_path, logger_name, **kwargs):
    """Handle anomalies by logging and sending email notifications.

    Args:
        log_path (str): Path to the log file.
        logger_name (str): Name of the logger.
        **kwargs: Keyword arguments including 'ti' (Airflow TaskInstance).

    Returns:
        None
    """
    ti = kwargs["ti"]
    validation_results = ti.xcom_pull(task_ids="validation", key="return_value")
    cleaned_data_path = ti.xcom_pull(task_ids="clean_data", key="return_value")

    logger = create_logger(log_path, logger_name)

    try:
        anomalies = [
            result for result in validation_results["results"] if not result["success"]
        ]
        anomaly_details = []

        if anomalies:
            logger.warning("Anomalies detected:")
            for anomaly in anomalies:
                info = {
                    "column": anomaly["expectation_config"]["kwargs"].get(
                        "column", "<unknown>"
                    ),
                    "expectation": anomaly["expectation_config"]["type"],
                    "unexpected_count": anomaly["result"].get("unexpected_count"),
                    "unexpected_percent": anomaly["result"].get("unexpected_percent"),
                    "partial_indexes": anomaly["result"].get(
                        "partial_unexpected_index_list", []
                    ),
                }
                msg = (
                    f"Column: {info['column']}, "
                    f"Expectation: {info['expectation']}, "
                    f"Unexpected Count: {info['unexpected_count']}, "
                    f"Unexpected Percent: {info['unexpected_percent']}, "
                    f"Partial Indexes: {info['partial_indexes']}"
                )
                logger.info(msg)
                anomaly_details.append(msg)

        # 🧠 Custom checks for behavior-based anomalies
        df = pd.read_csv(cleaned_data_path)

        # Flag very long threads
        long_threads = df.groupby("thread_id").size()
        suspicious = long_threads[long_threads > 25]
        if not suspicious.empty:
            detail = f"⚠️ {len(suspicious)} threads with more than 25 parts detected"
            logger.warning(detail)
            anomaly_details.append(detail)

        # Low volume of forwards — bad thread splits?
        type_distribution = df["email_type"].value_counts(normalize=True)
        if type_distribution.get("forward", 0) < 0.01:
            detail = (
                "⚠️ Less than 1% of emails are 'forward' — potential thread split issue"
            )
            logger.warning(detail)
            anomaly_details.append(detail)

        if anomaly_details:
            # Send email if there's anything actionable
            oauth_config = {
                "client_id": os.getenv("google_client_id"),
                "client_secret": os.getenv("google_client_secret"),
                "refresh_token": os.getenv("google_refresh_token"),
                "sender_email": os.getenv("sender_email"),
            }

            email_body = "Anomalies detected in email dataset:\n\n" + "\n".join(
                anomaly_details
            )
            success = send_email_notification(
                "Email Dataset Anomalies Detected",
                email_body,
                os.getenv("receiver_email"),
                oauth_config,
                logger,
            )
            if success:
                logger.info("📬 Email notification sent.")
            else:
                logger.error("❌ Failed to send email alert.")

        else:
            logger.info("✅ No actionable anomalies detected.")

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Error in Anomaly Handling: {e}", exc_info=True)
