from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path
import os
import re

# Add your project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.models.base import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata - this tells Alembic about your models
target_metadata = Base.metadata

def get_database_url() -> str:
    """Get database URL from environment and clean it for Alembic"""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise ValueError("DATABASE_URL not found in environment variables")
    
    # Remove asyncpg driver - Alembic uses psycopg2
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Remove any SSL parameters that psycopg2 doesn't understand
    # Common SSL params: sslmode, ssl, sslcert, sslkey, sslrootcert
    if '?' in url:
        # Split URL and query parameters
        base_url, query_string = url.split('?', 1)
        
        # Parse query parameters
        params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value
        
        # Remove problematic SSL params
        # Keep only safe params that psycopg2 understands
        safe_params = {}
        safe_keys = ['host', 'port', 'dbname', 'user', 'password']
        for key, value in params.items():
            if key.lower() in safe_keys:
                safe_params[key] = value
        
        # Rebuild URL without SSL params
        if safe_params:
            new_query = '&'.join([f"{k}={v}" for k, v in safe_params.items()])
            url = f"{base_url}?{new_query}"
        else:
            url = base_url
    
    return url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_database_url()
    
    # Override the sqlalchemy.url in the config with our environment URL
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
