import great_expectations as gx
import pandas as pd

from create_logger import createLogger


def define_expectations(CSV_PATH, context_root_dir, path, loggerName):
    """
    Defines data validation expectations for the dataset.

    Parameters:
        CSV_PATH (str): Path to the dataset.
        context_root_dir (str): Root directory for Great Expectations context.
        path (str): Path for logging.
        loggerName (str): Name of the logger.

    Returns:
        gx.ExpectationSuite: Configured expectation suite.
    """
    data_quality_logger = createLogger(path, loggerName)
    context = gx.get_context(context_root_dir=context_root_dir)
    try:
        data_quality_logger.info(f"Setting up Expectations in Suite")

        df = pd.read_csv(CSV_PATH)

        suite_name = "enron_expectation_suite"

        suite = gx.ExpectationSuite(name=suite_name)
        suite = context.suites.add_or_update(suite)

        # Define schema expectations
        not_null_columns = ["Message-ID", "From", "Body"]
        for column in not_null_columns:
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToNotBeNull(column=column)
            )

        email_regex = {
            "From": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "To": r"^(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:,\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$",
            "Cc": r"^(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:,\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$",
            "Bcc": r"^(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:,\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$",
        }
        for column, regex in email_regex.items():
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToMatchRegex(
                    column=column, regex=regex, mostly=0.95
                )
            )

        # Allow 5% null as body text is more important
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column="Date", mostly=0.95)
        )

        # Allow 10% null as body text and from is important
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column="X-From", mostly=0.90)
        )

        # Uniqueness check
        suite.add_expectation(
            gx.expectations.ExpectColumnUniqueValueCountToBeBetween(
                column="Message-ID", min_value=len(df), max_value=len(df)
            )
        )

        # Date Check [nan will be also in anamoly]
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInSet(
                column="Date",
                value_set=pd.date_range("1980-01-01", pd.Timestamp.now(), freq="D")
                .strftime("%Y-%m-%d")
                .tolist(),
            )
        )

        # Thread Integrity (Summary Task)
        # Expect Subject to be non-null for thread context
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column="Subject", mostly=0.95)
        )

        # Action Item Potential
        # Expect Body to contain actionable phrases/words for some emails
        action_phrases = r"(?i)\bmeeting\b|\bplease\b|\bneed\b|\baction\b|\bdo\b|\bsend\b|\breview\b|\burgent\b|\basap\b|\brespond\b|\bconfirm\b|\bfollow-up\b|\bcomplete\b|\bcheck\b"

        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToMatchRegex(
                column="Body",
                regex=action_phrases,
                mostly=0.50,
            )
        )

        # Reply Feasibility
        # Expect To to be present for drafting replies
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column="To",
                mostly=0.95,
            )
        )

        data_quality_logger.info(f"Created Expectation Suite successfully")
        return suite
    except Exception as e:
        data_quality_logger.error(f"Error in Expectations: {e}", exc_info=True)
