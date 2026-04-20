"""
FastAPI application entry point for Seaf Evaluation System.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.router import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Seaf Evaluation System")
    logger.info(f"Server: {settings.server_host}:{settings.server_port}")
    logger.info(f"Seaf API: {settings.seaf_api_base}")
    logger.info(f"LLM Provider: {settings.llm_provider}/{settings.llm_model}")
    yield
    logger.info("Shutting down Seaf Evaluation System")


# Create FastAPI application
app = FastAPI(
    title="Seaf Evaluation System",
    description="AI Agent Evaluation Platform for Seaf",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "seaf_api": settings.seaf_api_base,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Seaf Evaluation System",
        "version": "0.1.0",
        "docs": "/docs",
    }


def run():
    """Run the application using uvicorn."""
    import uvicorn
    uvicorn.run(
        "evaluation_system.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
    )


if __name__ == "__main__":
    run()
