import logging
import os

def setup_logger(log_file: str = "app.log", log_level: int = logging.INFO):
    """
    Set up the logger configuration.

    Args:
        log_file (str): The name of the log file to write logs to.
        log_level (int): The logging level (default is INFO).

    Returns:
        Logger: Configured logger instance.
    """
    # Create log directory if it does not exist
    log_directory = os.path.dirname(log_file)
    if log_directory and not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Configure the logger
    logging.basicConfig(
        filename=log_file,
        filemode='a',  # Append mode
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log_level,
    )

    logger = logging.getLogger(__name__)
    return logger

# # Example usage
# if __name__ == "__main__":
#     logger = setup_logger()  # You can customize the log file and level here
#     logger.info("Logger is set up and ready to use.")
