"""
SONAR-INTEL FastAPI Application Entry Point.
"""

import os
import datetime
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.logging_config import configure_logging
from backend.app.database.connection import init_db
from backend.app.api.upload import router as upload_router
from backend.app.api.analysis import router as analysis_router
from backend.app.api.contacts import router as contacts_router
from backend.app.api.review import router as review_router
from backend.app.api.reports import router as reports_router
from backend.app.api.demo import router as demo_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.pipeline import router as pipeline_router
from backend.app.api.inference import router as inference_router
from backend.app.api.ml import router as ml_router
from backend.app.api.anomalies import router as anomalies_router
from backend.app.api.active_learning import router as active_learning_router
from backend.app.api.analyst import router as analyst_router
from backend.app.api.resurvey import router as resurvey_router

from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    logger.info("SONAR-INTEL API started.")
    yield
    logger.info("SONAR-INTEL API shutting down.")

from backend.app.core.config import settings

app = FastAPI(
    title=settings.app.PROJECT_NAME,
    description="AI-Powered Side-Scan Sonar Marine Debris & Anomaly Detection API",
    version=settings.app.PROJECT_VERSION,
    lifespan=lifespan
)

# CORS Middleware configured centrally via settings.server.CORS_ORIGINS
origins = settings.server.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time

# Timing & Observability Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error occurred processing request.", "path": request.url.path}
        )
    process_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)
    return response


# Mount Routers
app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(contacts_router)
app.include_router(review_router)
app.include_router(reports_router)
app.include_router(demo_router)
app.include_router(dashboard_router)
app.include_router(pipeline_router)
app.include_router(inference_router)
app.include_router(ml_router)
app.include_router(anomalies_router)
app.include_router(active_learning_router)
app.include_router(analyst_router)
app.include_router(resurvey_router)

# Mount static demo/data directories if they exist
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/demo", exist_ok=True)


@app.get("/api/health", tags=["System"])
def health_check():
    """Operational health probe with model provenance and DB status."""
    import torch
    model_on_disk = os.path.exists(settings.MODEL_PATH)
    cuda_avail = torch.cuda.is_available()

    return {
        "status": "healthy",
        "service": "SONAR-INTEL API",
        "version": settings.app.PROJECT_VERSION,
        "environment": settings.app.ENV,
        "database": "active",
        "model": {
            "name": settings.MODEL_NAME,
            "version": settings.MODEL_VERSION,
            "weights_present": model_on_disk,
            "device": "cuda" if cuda_avail else "cpu"
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
