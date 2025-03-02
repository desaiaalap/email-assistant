import os
import tarfile
import warnings
from tqdm import tqdm

warnings.filterwarnings("ignore")

from create_logger import createLogger


def extract_enron_dataset(archive_path, extract_to, path, loggerName):
    """
    Extracts the Enron dataset from a compressed archive.

    Parameters:
        archive_path (str): Path to the compressed dataset file.
        extract_to (str): Directory where the extracted files will be stored.
        path (str): Path for logging.
        loggerName (str): Name of the logger.
    """
    data_extracting_logger = createLogger(path, loggerName)
    try:
        if os.path.exists(extract_to) and len(os.listdir(extract_to)) > 0:
            data_extracting_logger.info(
                "Dataset already extracted, skipping extraction."
            )
            return

        os.makedirs(extract_to, exist_ok=True)
        data_extracting_logger.info("Extracting the dataset...")

        # Extract the tar.gz file
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getmembers()
            with tqdm(total=len(members), desc="Extracting") as progress_bar:
                for member in members:
                    tar.extract(member, path=extract_to)
                    progress_bar.update(1)

        data_extracting_logger.info(
            f"Extraction complete! Files are saved in '{extract_to}'"
        )
        return extract_to
    except Exception as e:
        data_extracting_logger.error(f"Error extracting dataset: {e}", exc_info=True)


if __name__ == "__main__":
    extract_to = "./data_pipeline/data/dataset"
    archive_path = "./data_pipeline/data/enron_mail_20150507.tar.gz"
    path = "./data_pipeline/logs/data_extraction_log.log"
    loggerName = "data_extraction_logger"

    extract_enron_dataset(archive_path, extract_to, path, loggerName)
