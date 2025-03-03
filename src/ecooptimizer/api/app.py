from fastapi import FastAPI
from .routes import RefactorRouter, DetectRouter, LogRouter


app = FastAPI(title="Ecooptimizer")

# Include API routes
app.include_router(RefactorRouter)
app.include_router(DetectRouter)
app.include_router(LogRouter)


@app.get("/health")
async def ping():
    return {"status": "ok"}
