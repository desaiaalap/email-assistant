import os
import urllib.request
import warnings
import requests
from tqdm import tqdm

from create_logger import createLogger

warnings.filterwarnings("ignore")

DATA_DIR = "dataset"


def download_enron_dataset(url, save_path, path, loggerName):
    """
    Downloads the Enron dataset from a given URL and saves it locally.

    Parameters:
        url (str): URL of the dataset.
        save_path (str): Path to save the downloaded file.
        path (str): Path for logging.
        loggerName (str): Name of the logger.
    """
    data_downloading_logger = createLogger(path, loggerName)
    try:
        CHUNK_SIZE = 1024 * 1024

        # Check if dataset already exists
        if os.path.exists(save_path):
            data_downloading_logger.info(
                "Dataset archive already exists, skipping download."
            )
            return

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        data_downloading_logger.info("Downloading the Enron dataset...")

        # Stream download
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            with open(save_path, "wb") as file, tqdm(
                total=total_size, unit="B", unit_scale=True, desc="Downloading"
            ) as progress_bar:
                for chunk in response.iter_content(CHUNK_SIZE):
                    file.write(chunk)
                    progress_bar.update(len(chunk))
        data_downloading_logger.info(f"Dataset Downloaded Successfully at {save_path}")
        return save_path
    except Exception as e:
        data_downloading_logger.error(f"Error downloading dataset: {e}", exc_info=True)


if __name__ == "__main__":
    DATASET_URL = "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz"
    save_path = "./data_pipeline/data/enron_mail_20150507.tar.gz"
    path = "./data_pipeline/logs/data_downloading_log.log"
    loggerName = "data_downloading_logger"

    download_enron_dataset(DATASET_URL, save_path, path, loggerName)
