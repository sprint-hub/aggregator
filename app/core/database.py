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

db_url = settings.DATABASE_URL
if "?" in db_url:
    db_url = db_url.split("?")[0]

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

engine: AsyncEngine = create_async_engine(
    db_url,  # Use the cleaned URL string here
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  
    pool_recycle=300,   
    pool_timeout=30,
    connect_args={
        "ssl": ssl_context,
        "server_settings": {
            "application_name": "finref_backend",
        }
    }
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

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
    if settings.APP_ENV == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print(" Database tables created")


async def close_db():
    """Close database connection"""
    await engine.dispose()
