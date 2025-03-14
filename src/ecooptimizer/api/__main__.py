import logging
import sys
import uvicorn

from .app import app

from ..config import CONFIG


class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/health" not in record.getMessage()


# Apply the filter to Uvicorn's access logger
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


def start():
    # ANSI codes
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
    CONFIG["mode"] = "development" if "--dev" in sys.argv else "production"
    start()


def dev():
    CONFIG["mode"] = "development"
    start()


if __name__ == "__main__":
    main()
