import great_expectations as gx
import os

from data_quality_expectations import define_expectations
from data_quality_validation import validate_data
from data_quality_anomaly import handle_anomalies

from create_logger import createLogger


def setup_gx_context_and_logger(context_root_dir, path, loggerName):
    """
    Sets up Great Expectations validation environment and logging.

    Parameters:
        context_root_dir (str): Root directory for Great Expectations.
        path (str): Path for logging.
        loggerName (str): Logger name.

    Returns:
        str: Path to the initialized context.
    """
    data_quality_logger = createLogger(path, loggerName)
    try:
        os.makedirs(context_root_dir, exist_ok=True)
        context = gx.get_context(context_root_dir=context_root_dir)
        data_quality_logger.info(f"Successfully created gx-context and logger")
        return context_root_dir
    except Exception as e:
        data_quality_logger.error(f"Error creating gx context: {e}", exc_info=True)


if __name__ == "__main__":
    context_root_dir = "./data_pipeline/gx"
    data_quality_path = "./data_pipeline/logs/data_quality_log.log"
    data_qualty_loggerName = "data_quality_logger"
    anamoly_path = "./data_pipeline/logs/data_anomaly_log.log"
    anamoly_loggerName = "data_anomaly_logger"
    CSV_PATH = "./data_pipeline/data/enron_emails.csv"
    context_root_dir = setup_gx_context_and_logger(
        context_root_dir, data_quality_path, data_qualty_loggerName
    )
    suite = define_expectations(
        CSV_PATH, context_root_dir, data_quality_path, data_qualty_loggerName
    )
    validation_results = validate_data(
        CSV_PATH, suite, context_root_dir, data_quality_path, data_qualty_loggerName
    )
    handle_anomalies(validation_results, anamoly_path, anamoly_loggerName)
