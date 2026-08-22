import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.backend.app.core.config import settings
from apps.backend.app.core.database import Base, engine
from apps.backend.app.routers import scrapers, analytics, demo, chat, integrations
from apps.backend.app.services.worker_manager import WorkerManager

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webguardian")

# Create database tables on start (SQLite default fallback)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WebGuardian AI Control Plane",
    description="Autonomous Reliability Engineering for Web Data Infrastructure",
    version="1.0.0"
)

# Configure CORS for Next.js app communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon local runs. Can be restricted to localhost:3000 in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(scrapers.router)
app.include_router(analytics.router)
app.include_router(demo.router)
app.include_router(chat.router)
app.include_router(integrations.router)

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI: Application starting up")
    
    # Launch local worker queue loop as a concurrent background task
    asyncio.create_task(WorkerManager.start_local_worker_loop())
    logger.info("Worker: Local background task worker queue started successfully")

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "service": "WebGuardian AI Control Plane",
        "tagline": "The autonomous AI engineer that keeps web data pipelines alive."
    }
