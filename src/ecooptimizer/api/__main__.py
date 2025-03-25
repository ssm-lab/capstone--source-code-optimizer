"""Application entry point and server configuration for EcoOptimizer."""

import logging
import sys
import uvicorn

from .app import app
from ..config import CONFIG


class HealthCheckFilter(logging.Filter):
    """Filters out health check requests from access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Determines if a log record should be filtered.

        Args:
            record: The log record to evaluate

        Returns:
            bool: False if record contains health check, True otherwise
        """
        return "/health" not in record.getMessage()


# Apply the filter to Uvicorn's access logger
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


def start():
    """Starts the Uvicorn server with configured settings.

    Displays startup banner and handles different run modes.
    """
    # ANSI color codes
    RESET = "\u001b[0m"
    BLUE = "\u001b[36m"
    PURPLE = "\u001b[35m"

    mode_message = f"{CONFIG['mode'].upper()} MODE"
    msg_len = len(mode_message)

    print(f"\n\t\t\t***{'*'*msg_len}***")
    print(f"\t\t\t*  {BLUE}{mode_message}{RESET}  *")
    print(f"\t\t\t***{'*'*msg_len}***\n")

    if CONFIG["mode"] == "production":
        print(f"{PURPLE}hint: add --dev flag at the end to ignore energy checks\n")

    logging.info("🚀 Running EcoOptimizer Application...")
    logging.info(f"{'=' * 100}\n")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True,
        timeout_graceful_shutdown=2,
    )


def main():
    """Main entry point that sets mode based on command line arguments."""
    CONFIG["mode"] = "development" if "--dev" in sys.argv else "production"
    start()


def dev():
    """Development mode entry point that bypasses energy checks."""
    CONFIG["mode"] = "development"
    start()


if __name__ == "__main__":
    main()
