import logging
from pathlib import Path

# Base directory for logs and outputs
base_dir = Path(__file__).resolve().parents[2] / "ecooptimizer"
logs_dir = base_dir / "api/logs"

# Create logs directory if it doesn't exist
logs_dir.mkdir(parents=True, exist_ok=True)

# Log file path
log_file = logs_dir / "app.log"


# Configure logging
def setup_logging():
    """Set up logging configuration for the entire project(CLI or executable)"""
    # Reset existing handlers to avoid duplication
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configure root logger
    logging.basicConfig(
        filename=log_file,
        filemode="a",  # Append to log file
        level=logging.DEBUG,  # Log all levels DEBUG and above
        format="[%(levelname)s @ %(asctime)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add console output (optional, for debugging)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(console_handler)

    logging.info("Logging setup complete.")
