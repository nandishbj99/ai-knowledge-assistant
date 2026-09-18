import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.endpoints import router as api_router
from app.worker import run_worker

logger = logging.getLogger("ai-service-main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically start Redis Streams ingestion worker in background
    logger.info("Initializing background Redis Streams ingestion worker task...")
    worker_task = asyncio.create_task(run_worker())
    try:
        yield
    finally:
        logger.info("Stopping background ingestion worker...")
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount router under /api/v1 and root
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router)

@app.get("/")
def root():
    return {
        "service": "AI Knowledge Assistant RAG Engine",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_STR,
        "models": {
            "embeddings": f"{settings.EMBEDDING_MODEL} (768d)",
            "generation": settings.LLM_MODEL,
            "vision": settings.VISION_MODEL
        }
    }
