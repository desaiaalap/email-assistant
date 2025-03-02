import logging
import time
import os


def createLogger(path, name):
    """
    Creates and configures a logger to write logs to a specified file.

    Parameters:
        path (str): Path where the log file should be stored.
        name (str): Name of the logger.

    Returns:
        logging.Logger: logger instance.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(path)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    handler.formatter.converter = time.localtime
    logger.addHandler(handler)
    return logger
