#!/usr/bin/env python3
"""Run SQL migrations against NeonDB. Tracks applied migrations in schema_migrations."""

import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv()

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


async def run_migrations() -> None:
    """Execute migration files in order. Skips already-applied migrations."""
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is not set")

    conn = await asyncpg.connect(dsn)

    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
            )
            """
        )

        migration_files = sorted(
            f for f in MIGRATIONS_DIR.glob("*.sql") if f.name != "schema_migrations.sql"
        )

        for path in migration_files:
            version = path.stem
            existing = await conn.fetchval(
                "SELECT version FROM schema_migrations WHERE version = $1", version
            )
            if existing:
                print(f"Skip {path.name} (already applied)")
                continue

            sql = path.read_text()
            print(f"Apply {path.name}...")
            await conn.execute(sql)
            await conn.execute("INSERT INTO schema_migrations (version) VALUES ($1)", version)
            print(f"  OK: {version}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
