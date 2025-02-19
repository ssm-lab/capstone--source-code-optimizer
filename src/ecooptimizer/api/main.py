import logging
import sys
import uvicorn
from fastapi import FastAPI

from ..config import CONFIG

from .routes import detect_smells, show_logs, refactor_smell


class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/health" not in record.getMessage()


app = FastAPI(title="Ecooptimizer")

# Include API routes
app.include_router(detect_smells.router)
app.include_router(show_logs.router)
app.include_router(refactor_smell.router)


@app.get("/health")
async def ping():
    return {"status": "ok"}


# Apply the filter to Uvicorn's access logger
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


if __name__ == "__main__":
    CONFIG["mode"] = "development" if "--dev" in sys.argv else "production"

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
