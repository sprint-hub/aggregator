from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
from loguru import logger
import sys

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1.endpoints import auth
from app.api.v1.endpoints.agent import dashboard, codes, rewards, wallet, profile, network

# Setup logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL.upper()
)
if settings.LOG_FILE:
    logger.add(
        settings.LOG_FILE,
        rotation="500 MB",
        retention="10 days",
        level=settings.LOG_LEVEL.upper()
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    logger.info("Starting up FinRef API...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'local'}")

    # Initialize database (in production, use Alembic migrations)
    if settings.APP_ENV == "development":
        await init_db()
        logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down FinRef API...")
    await close_db()
    logger.info("Database connection closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Referral Management Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware (production security)
if settings.APP_ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Update with actual domains
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs" if settings.DEBUG else None,
        "version": "1.0.0"
    }


# Include Authentication Router
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])

# Include Agent Routers
app.include_router(
    dashboard.router, 
    prefix=f"{settings.API_V1_PREFIX}/agent/dashboard", 
    tags=["Agent Dashboard"]
)
app.include_router(
    codes.router, 
    prefix=f"{settings.API_V1_PREFIX}/agent/codes", 
    tags=["Agent Codes"]
)
app.include_router(
    rewards.router, 
    prefix=f"{settings.API_V1_PREFIX}/agent/rewards", 
    tags=["Agent Rewards"]
)
app.include_router(
    wallet.router, 
    prefix=f"{settings.API_V1_PREFIX}/agent/wallet", 
    tags=["Agent Wallet"]
)
app.include_router(
    profile.router, 
    prefix=f"{settings.API_V1_PREFIX}/agent/profile", 
    tags=["Agent Profile"]
)
app.include_router(
    network.router, 
    prefix=f"{settings.API_V1_PREFIX}/agent/network", 
    tags=["Agent Network"]
)

# Note: Admin and Shared routers will be added later
# app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["Admin"])
# app.include_router(shared.router, prefix=f"{settings.API_V1_PREFIX}/shared", tags=["Shared"])

logger.info("Routes registered")
logger.info(f"API available at http://localhost:8000{settings.API_V1_PREFIX}")