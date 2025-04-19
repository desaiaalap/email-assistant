"""
Module for defining data validation expectations using Great Expectations.

This module sets up expectations for email datasets, ensuring data integrity
and consistency in key columns like Message-ID, Date, From, To, and Body.

Functions:
    define_expectations(log_path, logger_name, **kwargs)
"""

import os
import sys
import great_expectations as gx
import pandas as pd

# Add scripts folder to sys.path
scripts_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
sys.path.append(scripts_folder)

# pylint: disable=wrong-import-position
from create_logger import create_logger


def _add_core_expectations(suite, df):
    """Helper to add core schema and email structure expectations."""
    not_null_columns = ["Message-ID", "From", "Body"]
    for column in not_null_columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column=column)
        )

    email_regex = {
        "From": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "To": (
            r"^(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            r"(?:,\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$"
        ),
        "Cc": (
            r"^(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            r"(?:,\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$"
        ),
        "Bcc": (
            r"^(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            r"(?:,\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$"
        ),
    }
    for column, regex in email_regex.items():
        if column in df.columns:
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToMatchRegex(
                    column=column, regex=regex, mostly=0.95
                )
            )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="Date", mostly=0.95)
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="X-From", mostly=0.90)
    )


def _add_additional_expectations(suite, df):
    """Helper to add additional expectations for date, subject, body, and cleaned columns."""
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="Date",
            value_set=pd.date_range("1980-01-01", pd.Timestamp.now(), freq="D")
            .strftime("%Y-%m-%d")
            .tolist(),
            mostly=0.90,
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="Subject", mostly=0.95)
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToMatchRegex(
            column="Body",
            regex=r"(?i)\b(meeting|please|need|action|do|send|review|urgent|asap|"
            r"respond|confirm|follow-up|complete|check)\b",
            mostly=0.50,
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="To", mostly=0.95)
    )

    if "thread_id" in df.columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column="thread_id", mostly=0.99
            )
        )
    if "email_part" in df.columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column="email_part", min_value=1
            )
        )
    if "email_type" in df.columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInSet(
                column="email_type",
                value_set=["original", "reply", "forward", "unknown"],
            )
        )


def define_expectations(log_path, logger_name, **kwargs):
    """
    Defines a Great Expectations suite for email data validation.

    Parameters:
        log_path (str): Path for logging.
        logger_name (str): Name of the logger.
        **kwargs: Additional arguments, including:
            - csv_path (str): Path to the CSV file.
            - context_root_dir (str): Great Expectations context root directory.
            - ti (optional): Airflow task instance for XCom.

    Returns:
        dict: JSON representation of the created expectation suite.

    Raises:
        ValueError: If required input parameters are empty or missing.
        FileNotFoundError: If the CSV file does not exist.
        pd.errors.EmptyDataError: If the CSV file is empty.
    """

    logger = create_logger(log_path, logger_name)
    context_root_dir = None
    csv_path = None

    try:
        ti = kwargs.get("ti")
        if ti:
            context_root_dir = ti.xcom_pull(
                task_ids="setup_gx_context_and_logger", key="return_value"
            )
            csv_path = ti.xcom_pull(task_ids="clean_data", key="return_value")
    except KeyError:
        if not all(
            [
                log_path,
                logger_name,
                kwargs.get("csv_path"),
                kwargs.get("context_root_dir"),
            ]
        ):
            # pylint: disable=raise-missing-from
            raise ValueError("One or more input parameters are empty")
        logger.info("Not running in Airflow context, using kwargs for paths.")

    context_root_dir = context_root_dir or kwargs.get("context_root_dir")
    csv_path = csv_path or kwargs.get("csv_path")

    if context_root_dir is None or csv_path is None:
        error_message = "Missing context_root_dir or csv_path from XCom or kwargs"
        logger.error(error_message)
        raise ValueError(error_message)

    context = gx.get_context(context_root_dir=context_root_dir)

    try:
        logger.info("Setting up Expectations in Suite")
        df = pd.read_csv(csv_path)

        if "thread_id" in df.columns and df["thread_id"].isna().sum() > 0:
            df["thread_id"].fillna("unknown_thread", inplace=True)
            logger.warning("Filled missing 'thread_id' with 'unknown_thread'.")

        if "email_type" in df.columns and df["email_type"].isna().sum() > 0:
            df["email_type"].fillna("unknown", inplace=True)
            logger.warning("Filled missing 'email_type' with 'unknown'.")

        suite = gx.ExpectationSuite(name="enron_expectation_suite")
        suite = context.suites.add_or_update(suite)

        _add_core_expectations(suite, df)
        _add_additional_expectations(suite, df)

        logger.info("Created Expectation Suite successfully")
        return suite.to_json_dict()

    except FileNotFoundError as exc:
        error_message = f"CSV file not found: {csv_path}"
        logger.error(error_message)
        raise FileNotFoundError(error_message) from exc
    except pd.errors.EmptyDataError as exc:
        error_message = f"CSV file is empty: {csv_path}"
        logger.error(error_message)
        raise pd.errors.EmptyDataError(error_message) from exc
    except Exception as exc:
        logger.error("Error in Expectations: %s", exc, exc_info=True)
        raise
