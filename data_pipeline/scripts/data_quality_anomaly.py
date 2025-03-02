import smtplib
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from create_logger import createLogger
import base64
import os
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

dotenv_path = os.path.join(ROOT_DIR, ".env")

load_dotenv(dotenv_path=dotenv_path)


def send_email_notification(subject, body, to_email, oauth_config, data_anomaly_logger):
    """
    Sends an email notification using OAuth2 authentication.

    Parameters:
        subject (str): Email subject.
        body (str): Email body content.
        to_email (str): Recipient email address.
        oauth_config (dict): OAuth credentials for authentication.
        data_anomaly_logger (Logger): Logger for recording email status.

    Returns:
        bool: True if email is sent successfully, False otherwise.
    """
    try:
        creds = Credentials(
            token=None,
            refresh_token=oauth_config["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
        )
        if not creds.valid or creds.token is None:
            if creds.refresh_token:
                creds.refresh(Request())
            else:
                data_anomaly_logger.error(f"No valid token or refresh token available")
                return False

        if not creds.valid or creds.token is None:
            data_anomaly_logger.error(
                f"OAuth token remains invalid after refresh attempt"
            )
            return False

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = oauth_config["sender_email"]
        msg["To"] = to_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            auth_string = (
                f"user={oauth_config['sender_email']}\1auth=Bearer {creds.token}\1\1"
            )
            auth_response = server.docmd(
                "AUTH", "XOAUTH2 " + base64.b64encode(auth_string.encode()).decode()
            )
            server.send_message(msg)
        return True
    except Exception as e:
        data_anomaly_logger.error(f"Failed to send email: {e}", exc_info=True)
        return False


def handle_anomalies(validation_results, path, loggerName):
    """
    Handles detected anomalies by logging details and sending email notifications.

    Parameters:
        validation_results (dict): Validation results containing anomaly details.
        path (str): Path for logging.
        loggerName (str): Name of the logger.
    """
    data_anomaly_logger = createLogger(path, loggerName)
    try:
        anomalies = [
            result for result in validation_results["results"] if not result["success"]
        ]
        if anomalies:
            anomaly_details = []
            data_anomaly_logger.warning("Anomalies detected:")

            # Log detected anomalies
            for anomaly in anomalies:
                expectation_type = anomaly["expectation_config"]["type"]
                column_name = anomaly["expectation_config"]["kwargs"]["column"]
                indexes = anomaly["result"].get("partial_unexpected_index_list", [])
                unexpected_count = anomaly["result"].get("unexpected_count")
                unexpected_percent = anomaly["result"].get("unexpected_percent")
                detail = (
                    f"Column: {column_name}, Expectation: {expectation_type}, "
                    f"Unexpected Count: {unexpected_count}, Unexpected Percent: {unexpected_percent}, "
                    f"Partial Indexes: {indexes}"
                )
                data_anomaly_logger.info(detail)
                anomaly_details.append(detail)

            oauth_config = {
                "client_id": os.getenv("google_client_id"),
                "client_secret": os.getenv("google_client_secret"),
                "refresh_token": os.getenv("google_refresh_token"),
                "sender_email": os.getenv("sender_email"),
            }

            # Send email notification
            email_body = "Anomalies detected in email dataset:\n\n" + "\n".join(
                anomaly_details
            )
            is_email_sent = send_email_notification(
                subject="Email Dataset Anomalies Detected",
                body=email_body,
                to_email=os.getenv("receiver_email"),
                oauth_config=oauth_config,
                data_anomaly_logger=data_anomaly_logger,
            )
            if not is_email_sent:
                data_anomaly_logger.error(f"Email Sending Unsuccessful....")
                return
            data_anomaly_logger.info("Email notification sent successfully.")
        else:
            data_anomaly_logger.info("No anomalies detected.")
    except Exception as e:
        data_anomaly_logger.error(f"Error in Anomaly Handling: {e}", exc_info=True)
