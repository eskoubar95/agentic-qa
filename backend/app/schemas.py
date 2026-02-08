"""Pydantic schemas for API request/response."""

from uuid import UUID

from pydantic import BaseModel, Field


class TestStep(BaseModel):
    """Single step in a test definition."""

    action: str  # navigate | click | fill | verify
    instruction: str
    advanced_selector: str | None = None
    target: str | None = None
    value: str | None = None
    expected: str | None = None


class TestDefinition(BaseModel):
    """Test definition with steps."""

    steps: list[TestStep] = []


class TestCreate(BaseModel):
    """Payload for creating a test."""

    name: str
    url: str
    definition: dict = Field(default_factory=dict)
    auto_handle_popups: bool = True


class TestUpdate(BaseModel):
    """Payload for updating a test."""

    name: str | None = None
    url: str | None = None
    definition: dict | None = None
    auto_handle_popups: bool | None = None


class TestResponse(BaseModel):
    """Test in API response."""

    id: UUID
    user_id: UUID
    name: str
    url: str
    definition: dict
    auto_handle_popups: bool

    class Config:
        from_attributes = True


class RunTestRequest(BaseModel):
    """Payload for POST /test/run."""

    test_id: UUID


class RunTestResponse(BaseModel):
    """Response for POST /test/run."""

    run_id: UUID


class TestRunResponse(BaseModel):
    """Test run in API response."""

    id: UUID
    test_id: UUID
    status: str
    started_at: str | None
    completed_at: str | None
    duration_ms: int | None
    screenshots: list | None
    logs: list | None
    step_results: list | None
    self_healed: bool
    llm_calls: int
    cost_usd: float
    error: str | None
    error_step: int | None
    created_at: str

    class Config:
        from_attributes = True
