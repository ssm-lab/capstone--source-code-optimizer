"""Application entry point and server configuration for EcoOptimizer."""

import argparse
import logging
import uvicorn

from ecooptimizer.api.app import app
from ecooptimizer.config import CONFIG


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


def start(host: str = "127.0.0.1", port: int = 8000):
    """Starts the Uvicorn server with configured settings.

    Displays startup banner and handles different run modes.
    """
    # ANSI color codes
    RESET = "\u001b[0m"
    BLUE = "\u001b[36m"
    PURPLE = "\u001b[35m"

    mode_message = f"{CONFIG['mode'].upper()} MODE"
    msg_len = len(mode_message)

    print(f"\n\t\t\t***{'*' * msg_len}***")
    print(f"\t\t\t*  {BLUE}{mode_message}{RESET}  *")
    print(f"\t\t\t***{'*' * msg_len}***\n")

    if CONFIG["mode"] == "production":
        print(f"{PURPLE}hint: add --dev flag at the end to ignore energy checks\n")

    logging.info("🚀 Running EcoOptimizer Application...")
    logging.info(f"{'=' * 100}\n")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        timeout_graceful_shutdown=2,
    )


def main():
    """Main entry point that sets mode based on command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    CONFIG["mode"] = "development" if args.dev else "production"
    start(args.host, args.port)


def dev():
    """Development mode entry point that bypasses energy checks."""
    CONFIG["mode"] = "development"
    start()


if __name__ == "__main__":
    main()
