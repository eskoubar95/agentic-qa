"""AsyncPG connection pool for FastAPI read/write operations."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg

from app.config import get_settings

pool: asyncpg.Pool | None = None


async def init_db() -> None:
    """Create connection pool on startup. Skips if DATABASE_URL is empty."""
    global pool
    dsn = get_settings().DATABASE_URL
    if not dsn:
        return
    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=2,
        max_size=10,
        command_timeout=60,
    )


async def close_db() -> None:
    """Close connection pool on shutdown."""
    global pool
    if pool:
        await pool.close()
        pool = None


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Acquire a connection from the pool. Use as context manager."""
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)


async def health_check() -> bool:
    """Verify database connectivity. Returns True if healthy."""
    if pool is None:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False
