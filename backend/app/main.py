from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, health_check, init_db
from app.redis_client import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events (startup/shutdown)."""
    init_redis()
    await init_db()
    try:
        yield
    finally:
        await close_db()
        await close_redis()


def _get_cors_origins() -> list[str]:
    """Return CORS origins. Never returns ['*'] when credentials are used."""
    origins = get_settings().CORS_ORIGINS.strip()
    if not origins:
        return ["http://localhost:3000"]
    return [o.strip() for o in origins.split(",") if o.strip()]


app = FastAPI(
    title="Agentic QA Backend",
    version="0.1.0",
    description="API for Agentic QA platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.routers import runs, tests

app.include_router(tests.router)
app.include_router(runs.router)


@app.get("/health")
async def health() -> dict:
    """Health check for Railway and load balancers. Includes DB and Redis."""
    from app.redis_client import is_redis_available

    db_ok = await health_check()
    redis_ok = is_redis_available()
    status = "healthy" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "service": "agentic-qa-backend",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
    }
