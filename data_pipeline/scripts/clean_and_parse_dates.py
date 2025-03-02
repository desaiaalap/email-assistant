import os
import pandas as pd
import email
import re

from create_logger import createLogger


def clean_and_parse_dates(CSV_PATH, path, loggerName):
    """
    Cleans and processes the 'Date' column in the DataFrame by:
    - Removing timezone abbreviations
    - Standardizing date formats
    - Converting to datetime format
    - Extracting day, time, and date components

    Parameters:
        df (pd.DataFrame): DataFrame containing a 'Date' column.

    Returns:
        pd.DataFrame: DataFrame with cleaned and parsed date-related columns.
    """

    data_preprocessing_logger = createLogger(path, loggerName)
    try:

        df = pd.read_csv(CSV_PATH)

        # Remove timezone abbreviation from 'Date' column
        df["Original_Timezone"] = df["Date"].str.extract(
            r"(\s\([A-Za-z]{3,4}\))$", expand=False
        )

        data_preprocessing_logger.info(f"Created Original_Timezone in Dataframe")

        df["Date"] = df["Date"].str.replace(r"\s\([A-Za-z]{3,4}\)$", "", regex=True)

        # Function to clean and standardize date strings
        def clean_date_string(date_str):
            if pd.isna(date_str):
                return date_str

            # Add leading zero to single-digit day if missing
            date_str = re.sub(r"(\w{3},\s)(\d{1})(\s)", r"\g<1>0\2\3", date_str)

            # Expand 2-digit years
            date_str = re.sub(
                r"(\s)(\d{1,2})(\s\d{2}:\d{2}:\d{2})",
                lambda x: f'{x.group(1)}{"20" if int(x.group(2)) < 50 else "19"}{x.group(2)}{x.group(3)}',
                date_str,
            )

            return date_str

        df["Cleaned_Date"] = df["Date"].apply(clean_date_string)

        data_preprocessing_logger.info(f"Cleaned Date in Dataframe")

        df["Parsed_Date"] = pd.to_datetime(
            df["Cleaned_Date"], errors="coerce", utc=True
        )

        data_preprocessing_logger.info(f"Converted to datetime format in Dataframe")

        df["Day"] = df["Parsed_Date"].dt.day_name()
        data_preprocessing_logger.info(f"Created Day in Dataframe")

        df["Time"] = df["Parsed_Date"].dt.time
        data_preprocessing_logger.info(f"Created Time in Dataframe")

        df["Date"] = df["Parsed_Date"].dt.date
        data_preprocessing_logger.info(f"Created Date in Dataframe")

        df.drop(columns=["Parsed_Date", "Cleaned_Date"], inplace=True)
        data_preprocessing_logger.info(f"Droped Temporary Columns from Dataframe")

        df.to_csv(CSV_PATH, index=False)

        data_preprocessing_logger.info(
            "DataFrame saved to enron_emails.csv successfully."
        )

        return CSV_PATH
    except Exception as e:
        data_preprocessing_logger.error(
            f"Error in cleaning and parsing dates: {e}", exc_info=True
        )


if __name__ == "__main__":

    CSV_PATH = "./data_pipeline/data/enron_emails.csv"

    path = "./data_pipeline/logs/data_preprocessing_log.log"
    loggerName = "data_preprocessing_logger"

    CSV_PATH = clean_and_parse_dates(path, loggerName, CSV_PATH)
