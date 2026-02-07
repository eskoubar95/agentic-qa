from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events (startup/shutdown)."""
    yield


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


@app.get("/health")
def health() -> dict[str, str]:
    """Health check for Railway and load balancers."""
    return {"status": "healthy", "service": "agentic-qa-backend"}
