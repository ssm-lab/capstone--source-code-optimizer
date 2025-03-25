"""Main FastAPI application setup and health check endpoint."""

from fastapi import FastAPI
from .routes import RefactorRouter, DetectRouter, LogRouter


app = FastAPI(
    title="Ecooptimizer",
    description="API for detecting and refactoring energy-inefficient Python code",
)

# Register all API routers
app.include_router(RefactorRouter, tags=["refactoring"])
app.include_router(DetectRouter, tags=["detection"])
app.include_router(LogRouter, tags=["logging"])


@app.get("/health")
async def ping():
    """Check if the API service is running.

    Returns:
        dict: Simple status response {'status': 'ok'}
    """
    return {"status": "ok"}
