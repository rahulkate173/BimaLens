from typing import Any, Literal

from pydantic import BaseModel, Field


class OcrCompleteWebhook(BaseModel):
    job_id: str
    policy_id: str
    status: Literal["completed", "failed"]
    analysis_data: dict[str, Any] | None = None
    annotated_pdf_public_id: str | None = None
    error: str | None = None


class ClauseToolRequest(BaseModel):
    policy_id: str
    question: str | None = None
