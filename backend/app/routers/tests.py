"""Tests CRUD API."""

import json
import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.schemas import TestCreate, TestResponse, TestUpdate

router = APIRouter(prefix="/tests", tags=["tests"])


def _ensure_dict(val):
    """Convert JSONB value (dict | str) to dict."""
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        return json.loads(val) if val else {}
    return {}

# MVP: hardcoded user
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=TestResponse, status_code=201)
async def create_test(payload: TestCreate):
    """Create a new test."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tests (user_id, name, url, definition, auto_handle_popups)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, name, url, definition, auto_handle_popups
            """,
            DEMO_USER_ID,
            payload.name,
            payload.url,
            json.dumps(payload.definition),
            payload.auto_handle_popups,
        )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create test")
    return TestResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        url=row["url"],
        definition=_ensure_dict(row["definition"]),
        auto_handle_popups=row["auto_handle_popups"],
    )


@router.get("", response_model=list[TestResponse])
async def list_tests():
    """List all tests for the demo user."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, name, url, definition, auto_handle_popups
            FROM tests
            WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            DEMO_USER_ID,
        )
    return [
        TestResponse(
            id=r["id"],
            user_id=r["user_id"],
            name=r["name"],
            url=r["url"],
            definition=_ensure_dict(r["definition"]),
            auto_handle_popups=r["auto_handle_popups"],
        )
        for r in rows
    ]


@router.get("/{test_id}", response_model=TestResponse)
async def get_test(test_id: UUID):
    """Get a test by ID."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, name, url, definition, auto_handle_popups
            FROM tests
            WHERE id = $1 AND user_id = $2
            """,
            test_id,
            DEMO_USER_ID,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Test not found")
    return TestResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        url=row["url"],
        definition=_ensure_dict(row["definition"]),
        auto_handle_popups=row["auto_handle_popups"],
    )


@router.put("/{test_id}", response_model=TestResponse)
async def update_test(test_id: UUID, payload: TestUpdate):
    """Update a test."""
    updates = []
    values = []
    i = 1
    if payload.name is not None:
        updates.append(f"name = ${i}")
        values.append(payload.name)
        i += 1
    if payload.url is not None:
        updates.append(f"url = ${i}")
        values.append(payload.url)
        i += 1
    if payload.definition is not None:
        updates.append(f"definition = ${i}")
        values.append(json.dumps(payload.definition))
        i += 1
    if payload.auto_handle_popups is not None:
        updates.append(f"auto_handle_popups = ${i}")
        values.append(payload.auto_handle_popups)
        i += 1
    if not updates:
        return await get_test(test_id)
    updates.append("updated_at = NOW()")
    values.extend([test_id, DEMO_USER_ID])
    id_param = i
    user_param = i + 1
    async with get_connection() as conn:
        row = await conn.fetchrow(
            f"""
            UPDATE tests
            SET {", ".join(updates)}
            WHERE id = ${id_param} AND user_id = ${user_param}
            RETURNING id, user_id, name, url, definition, auto_handle_popups
            """,
            *values,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Test not found")
    return TestResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        url=row["url"],
        definition=_ensure_dict(row["definition"]),
        auto_handle_popups=row["auto_handle_popups"],
    )


@router.delete("/{test_id}", status_code=204)
async def delete_test(test_id: UUID):
    """Delete a test."""
    async with get_connection() as conn:
        result = await conn.execute(
            "DELETE FROM tests WHERE id = $1 AND user_id = $2",
            test_id,
            DEMO_USER_ID,
        )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Test not found")
