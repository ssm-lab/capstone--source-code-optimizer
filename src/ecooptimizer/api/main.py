import logging
import uvicorn
from fastapi import FastAPI

from ..config import CONFIG

from .routes import detect_smells, show_logs, refactor_smell


app = FastAPI(title="Ecooptimizer")

# Include API routes
app.include_router(detect_smells.router)
app.include_router(show_logs.router)
app.include_router(refactor_smell.router)

if __name__ == "__main__":
    CONFIG["mode"] = "production"

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
