"""Typed contracts shared by the OCR API, LangGraph pipeline, and worker."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field


class Category(str, Enum):
    COVERAGE = "Coverage"
    EXCLUSION = "Exclusion"
    FINANCIAL = "Financial"
    OBLIGATION = "Obligation"
    METADATA = "Metadata"
    RED_FLAG = "Red_Flag"


class JobStatus(str, Enum):
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessRequest(BaseModel):
    policy_id: str = Field(pattern=r"^[a-fA-F0-9]{24}$")
    pdf_url: AnyHttpUrl


class ProcessResponse(BaseModel):
    status: JobStatus = JobStatus.ACCEPTED
    job_id: str


class ExtractedPoint(BaseModel):
    category: Category
    point_summary: str = Field(min_length=1, max_length=500)
    exact_quote: str = Field(min_length=4, max_length=3000)
    continuity_flag: Literal[
        "NONE", "CONTINUED_FROM_PREVIOUS", "CONTINUES_ON_NEXT"
    ] = "NONE"


class PageClassification(BaseModel):
    page_number: int = Field(ge=1)
    section_title: str = Field(default="", max_length=300)
    extracted_points: list[ExtractedPoint] = Field(default_factory=list, max_length=30)


class TextBlock(BaseModel):
    text: str
    bbox: list[float] = Field(min_length=4, max_length=4)
    confidence: float | None = Field(default=None, ge=0, le=1)


class OCRPageResult(BaseModel):
    page_number: int
    method: str
    text: str
    blocks: list[TextBlock] = Field(default_factory=list)
    confidence: float | None = None


class PipelineState(BaseModel):
    job_id: str
    policy_id: str
    pdf_url: str
    pdf_path: str
    page_texts: list[OCRPageResult] = Field(default_factory=list)
    classifications: list[PageClassification] = Field(default_factory=list)
    annotated_pdf_path: str | None = None
    annotated_pdf_public_id: str | None = None
    analysis_data: dict | None = None
    error: str | None = None


class CallbackPayload(BaseModel):
    job_id: str
    policy_id: str
    status: Literal["completed", "failed"]
    analysis_data: dict | None = None
    annotated_pdf_public_id: str | None = None
    error: str | None = None
