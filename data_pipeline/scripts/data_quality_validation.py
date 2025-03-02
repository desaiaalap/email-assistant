import great_expectations as gx
import pandas as pd

from create_logger import createLogger


def validate_data(CSV_PATH, suite, context_root_dir, path, loggerName):
    """
    Performs data validation using Great Expectations.

    Parameters:
        CSV_PATH (str): Path to the input CSV file.
        suite (str): Name of the Great Expectations validation suite.
        context_root_dir (str): Root directory of the Great Expectations context.
        path (str): Path for logging.
        loggerName (str): Name of the logger.

    Returns:
        validation_result (dict): Validation results containing validation outcomes.
    """
    context = gx.get_context(context_root_dir=context_root_dir)
    data_quality_logger = createLogger(path, loggerName)
    try:
        df = pd.read_csv(CSV_PATH)
        data_quality_logger.info(f"Setting up Validation Definition to run...")
        data_source_name = "enron_data_source"
        try:
            data_source = context.data_sources.get(data_source_name)
        except Exception:
            data_source = context.data_sources.add_pandas(data_source_name)
        data_asset_name = "enron_email_data"
        try:
            data_asset = data_source.get_asset(data_asset_name)
        except Exception:
            data_asset = data_source.add_dataframe_asset(name=data_asset_name)
        batch_definition_name = "enron_batch_definition"
        try:
            batch_definition = data_asset.get_batch_definition(batch_definition_name)
        except Exception:
            batch_definition = data_asset.add_batch_definition_whole_dataframe(
                batch_definition_name
            )

        batch_parameters = {"dataframe": df}
        batch = batch_definition.get_batch(batch_parameters=batch_parameters)

        validation_definition_name = "enron_validation_definition"

        validation_definition = gx.ValidationDefinition(
            data=batch_definition, suite=suite, name=validation_definition_name
        )

        validation_definition = context.validation_definitions.add_or_update(
            validation_definition
        )

        validation_result = validation_definition.run(batch_parameters=batch_parameters)

        data_quality_logger.info(f"Validations ran successfully")

        return validation_result
    except Exception as e:
        data_quality_logger.error(f"Error in Validation: {e}", exc_info=True)
