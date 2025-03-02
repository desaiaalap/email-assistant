import os
import pandas as pd
import email
import sys

from create_logger import createLogger


# Extracts metadata and full email body from an email file.
def extract_email_data(email_path, data_preprocessing_logger, HEADER_KEYS):
    """
    Extracts metadata and full email body from an email file.

    Parameters:
        email_path (str): Path to the email file.
        data_preprocessing_logger (Logger): Logger instance.
        HEADER_KEYS (list): List of email header fields to extract.

    Returns:
        dict: Extracted email metadata and body.
    """
    try:
        with open(email_path, "r", encoding="utf-8", errors="ignore") as f:
            msg = email.message_from_file(f)

        # Extract metadata
        email_data = {key: msg.get(key, None) for key in HEADER_KEYS}

        # Extract the email body (handle multipart and plain text emails)
        body_parts = []
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":  # Extract plain text content
                    try:
                        body_parts.append(
                            part.get_payload(decode=True).decode(errors="ignore")
                        )
                    except Exception:
                        pass  # Skip problematic encodings
        else:
            try:
                body_parts.append(msg.get_payload(decode=True).decode(errors="ignore"))
            except Exception:
                pass  # Skip problematic encodings

        # Join all body parts, keeping forwarded messages intact
        email_data["Body"] = "\n".join(body_parts).strip()
        return email_data
    except Exception as e:
        data_preprocessing_logger.error(
            f"Error processing email {email_path}: {e}", exc_info=True
        )
        return None


# Loop through all folders and extract emails into a DataFrame.
def process_enron_emails(data_dir, path, loggerName, CSV_PATH):
    """
    Processes all email files in the dataset and extracts relevant information.

    Parameters:
        data_dir (str): Directory containing email files.
        path (str): Path for logging.
        loggerName (str): Name of the logger.
        CSV_PATH (str): Path to save the processed emails as CSV.

    Returns:
        str: Path to the saved CSV file.
    """
    try:
        HEADER_KEYS = [
            "Message-ID",
            "Date",
            "From",
            "To",
            "Subject",
            "Cc",
            "Bcc",
            "X-From",
            "X-To",
            "X-Cc",
        ]
        email_list = []
        total_files = 0

        data_preprocessing_logger = createLogger(path, loggerName)

        if not os.path.exists(data_dir):
            data_preprocessing_logger.error(f"Directory {data_dir} does not exist!")
            return pd.DataFrame()

        data_preprocessing_logger.info(f"Processing emails in: {data_dir}")

        for root, _, files in os.walk(data_dir):

            for file in files:
                email_path = os.path.join(root, file)
                total_files += 1
                try:
                    email_data = extract_email_data(
                        email_path, data_preprocessing_logger, HEADER_KEYS
                    )
                    email_list.append(email_data)
                    if total_files % 10000 == 0:
                        sys.stdout.write(f"\rProcessed {total_files} emails so far")
                        sys.stdout.flush()
                except Exception as e:
                    data_preprocessing_logger.error(
                        f"Error processing {email_path}: {e}"
                    )

        data_preprocessing_logger.info(f"Total emails processed: {total_files}")

        # Convert to Pandas DataFrame
        df = pd.DataFrame(email_list)
        data_preprocessing_logger.info("DataFrame created successfully.")

        df.to_csv(CSV_PATH, index=False)
        data_preprocessing_logger.info(
            f"DataFrame saved to {CSV_PATH} successfully in process_enron_emails."
        )

        return CSV_PATH
    except Exception as e:
        data_preprocessing_logger.error(
            f"Error in process_enron_emails function: {e}", exc_info=True
        )
        return None


if __name__ == "__main__":
    # Path to the extracted dataset
    MAILDIR_PATH = "./data_pipeline/data/dataset/maildir"

    CSV_PATH = "./data_pipeline/data/enron_emails.csv"

    path = "./data_pipeline/logs/data_preprocessing_log.log"
    loggerName = "data_preprocessing_logger"

    # Process all emails
    df_enron = process_enron_emails(MAILDIR_PATH, path, loggerName, CSV_PATH)
