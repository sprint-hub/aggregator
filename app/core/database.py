from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.core.config import settings
import ssl

# Create async engine with Neon-specific settings
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  
    pool_recycle=300,   
    pool_timeout=30,
    # Neon specific: SSL is required
    connect_args={
        "ssl": ssl.create_default_context(),
        "server_settings": {
            "application_name": "finref_backend",
        }
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create tables"""
    # For production, use Alembic migrations instead
    # This is only for development
    if settings.APP_ENV == "development":
        async with engine.begin() as conn:
            # Drop all tables (careful in production!)
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            print(" Database tables created")


async def close_db():
    """Close database connection"""
    await engine.dispose()