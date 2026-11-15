from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PolicyUploadResponse(BaseModel):
    policy_id: str
    status: str
    filename: str


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    language: str = Field(default="English", min_length=2, max_length=30)


class AskSource(BaseModel):
    page: int
    section: str = ""
    quote: str
    category: str = "Metadata"


class AskResponse(BaseModel):
    answer: str
    sources: list[AskSource] = Field(default_factory=list)
    provider: str | None = None


class FitRequest(BaseModel):
    age: int | None = Field(default=None, ge=18, le=120)
    dependents: int = Field(default=0, ge=0, le=30)
    location: str | None = Field(default=None, max_length=100)
    liabilities: str | None = Field(default=None, max_length=500)
    goal: str = Field(min_length=2, max_length=200)


class FitResponse(BaseModel):
    summary: str
    observations: list[AskSource] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    provider: str | None = None


class PolicyResponse(BaseModel):
    id: str
    filename: str
    uploaded_at: datetime
    status: Literal["processing", "ready", "failed"]
    error: str | None = None
    analysis: dict[str, Any] | None = None


class PdfLinkResponse(BaseModel):
    url: str
    expires_in: int


class ClaimChecklistResponse(BaseModel):
    items: list[AskSource] = Field(default_factory=list)
    disclaimer: str


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
