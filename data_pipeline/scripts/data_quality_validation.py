"""
Module for data validation using Great Expectations.

This module validates email datasets against predefined data expectations,
ensuring data quality, consistency, and schema integrity.

Functions:
    validate_data(log_path, logger_name, **kwargs)
"""

# Disabled duplicate-code as it is giving silly error like,
#  error_message = f"CSV file not found: {csv_path}"
#  data_quality_logger.error(error_message)
#  the above two lines are same
# pylint: disable=duplicate-code
import os
import sys
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite

# Add scripts folder to sys.path
scripts_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
sys.path.append(scripts_folder)

# pylint: disable=wrong-import-position
from create_logger import create_logger


def _setup_data_source_and_asset(context, logger):
    """Helper to set up or retrieve data source and asset."""
    try:
        data_source = context.data_sources.get(name="enron_data_source")
    except gx.exceptions.DataContextError:
        data_source = context.data_sources.add_pandas(name="enron_data_source")
        logger.info("Created new data source: enron_data_source")

    try:
        data_asset = data_source.get_asset(name="enron_email_data")
    except gx.exceptions.DataContextError:
        data_asset = data_source.add_dataframe_asset(name="enron_email_data")
        logger.info("Created new data asset: enron_email_data")

    return data_source, data_asset


def _setup_batch_definition(data_asset, logger):
    """Helper to set up or retrieve batch definition."""
    try:
        batch_definition = data_asset.get_batch_definition("enron_batch_definition")
    except gx.exceptions.DataContextError:
        batch_definition = data_asset.add_batch_definition_whole_dataframe(
            "enron_batch_definition"
        )
        logger.info("Created new batch definition: enron_batch_definition")
    return batch_definition


# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
def validate_data(log_path, logger_name, **kwargs):
    """
    Validates cleaned Enron email data against expectations using Great Expectations.

    Parameters:
        log_path (str): Path for logging.
        logger_name (str): Name of the logger.
        **kwargs: Additional arguments, including:
            - csv_path (str): Path to the CSV file.
            - suite (dict or ExpectationSuite): Expectation suite or its JSON dict.
            - context_root_dir (str): Great Expectations context root directory.
            - ti (optional): Airflow task instance for XCom.

    Returns:
        dict: Validation results with success status, results count, and unexpected count.

    Raises:
        ValueError: If required inputs (csv_path, suite, context_root_dir) are missing.
        FileNotFoundError: If the CSV file does not exist.
        pd.errors.EmptyDataError: If the CSV file is empty.
        gx.exceptions.DataContextError: If Great Expectations setup fails.
        gx.exceptions.ValidationError: If validation fails.
    """
    logger = create_logger(log_path, logger_name)
    csv_path = None
    suite_dict = None
    context_root_dir = None

    try:
        ti = kwargs.get("ti")
        if ti:
            csv_path = ti.xcom_pull(task_ids="clean_data", key="return_value")
            suite_dict = ti.xcom_pull(task_ids="expectation_suite", key="return_value")
            context_root_dir = ti.xcom_pull(
                task_ids="setup_gx_context_and_logger", key="return_value"
            )
    except KeyError:
        logger.info("Not running in Airflow context, using kwargs for inputs.")

    csv_path = csv_path or kwargs.get("csv_path")
    suite_dict = suite_dict or kwargs.get("suite")
    context_root_dir = context_root_dir or kwargs.get("context_root_dir")

    if not all([csv_path, suite_dict, context_root_dir]):
        error_message = (
            "Missing one or more required inputs: csv_path, suite, or context_root_dir"
        )
        logger.error(error_message)
        raise ValueError(error_message)

    suite = (
        ExpectationSuite(**suite_dict) if isinstance(suite_dict, dict) else suite_dict
    )
    context = gx.get_context(context_root_dir=context_root_dir)

    try:
        df = pd.read_csv(csv_path)
        logger.info("Starting validation with Great Expectations...")

        _, data_asset = _setup_data_source_and_asset(context, logger)
        batch_definition = _setup_batch_definition(data_asset, logger)
        batch_definition.get_batch(batch_parameters={"dataframe": df})

        validation_definition = gx.ValidationDefinition(
            data=batch_definition, suite=suite, name="enron_validation_definition"
        )
        validation_definition = context.validation_definitions.add_or_update(
            validation_definition
        )
        validation_result = validation_definition.run(
            batch_parameters={"dataframe": df}
        )
        result_dict = validation_result.to_json_dict()
        logger.info("Validations completed successfully")

        return {
            "success": result_dict["success"],
            "results": result_dict["results"],
            "expectation_suite_name": suite.name,
            "results_count": len(result_dict["results"]),
            "unexpected_count": sum(
                r["result"].get("unexpected_count", 0)
                for r in result_dict["results"]
                if "result" in r
            ),
        }
    # pylint: disable=logging-fstring-interpolation
    except FileNotFoundError as exc:
        logger.error(f"CSV file not found: {csv_path}")
        raise FileNotFoundError(f"CSV file not found: {csv_path}") from exc
    except pd.errors.EmptyDataError as exc:
        logger.error(f"CSV file is empty: {csv_path}")
        raise pd.errors.EmptyDataError(f"CSV file is empty: {csv_path}") from exc
    except gx.exceptions.DataContextError as exc:
        logger.error(f"Error in Great Expectations data setup: {exc}", exc_info=True)
        raise
    except gx.exceptions.ValidationError as exc:
        logger.error(f"Validation run failed: {exc}", exc_info=True)
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error(f"Unexpected error in validation: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    # Example usage (not typically run standalone)
    from get_project_root import project_root
    from data_quality_expectations import define_expectations

    PROJECT_ROOT_DIR = project_root()
    CSV_PATH = f"{PROJECT_ROOT_DIR}/data_pipeline/data/enron_emails.csv"
    CONTEXT_ROOT_DIR = f"{PROJECT_ROOT_DIR}/data_pipeline/gx"
    LOG_PATH = f"{PROJECT_ROOT_DIR}/data_pipeline/logs/data_quality_log.log"
    LOGGER_NAME = "data_quality_logger"

    try:
        SUITE = define_expectations(
            log_path=LOG_PATH,
            logger_name=LOGGER_NAME,
            csv_path=CSV_PATH,
            context_root_dir=CONTEXT_ROOT_DIR,
        )
        RESULT = validate_data(
            log_path=LOG_PATH,
            logger_name=LOGGER_NAME,
            csv_path=CSV_PATH,
            suite=SUITE,
            context_root_dir=CONTEXT_ROOT_DIR,
        )
        print(
            "Validation completed successfully:", RESULT["success"]
        )  # pylint: disable=no-member
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
