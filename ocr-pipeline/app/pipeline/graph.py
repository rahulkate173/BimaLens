"""LangGraph workflow for policy OCR, clause extraction, and PDF annotations."""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, TypedDict

import cloudinary
import cloudinary.uploader
import pymupdf as fitz
from langgraph.graph import END, START, StateGraph
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.models.schemas import OCRPageResult
from app.pipeline.document import annotate_pdf, download_pdf, extract_document
from app.pipeline.llm import classify_pages

logger = logging.getLogger(__name__)


class GraphState(TypedDict, total=False):
    job_id: str
    policy_id: str
    pdf_url: str
    pdf_path: str
    annotated_pdf_path: str
    pages: list[OCRPageResult]
    classifications: list[dict[str, Any]]
    analysis_data: dict[str, Any]
    annotated_pdf_public_id: str


async def download_node(state: GraphState) -> dict[str, str]:
    path = Path(state["pdf_path"])
    await download_pdf(state["pdf_url"], path)
    return {"pdf_path": str(path)}


async def extract_node(state: GraphState) -> dict[str, list[OCRPageResult]]:
    pages = await extract_document(Path(state["pdf_path"]))
    if not pages:
        raise ValueError("The PDF did not contain any readable pages.")
    if not any(page.text.strip() for page in pages):
        raise ValueError("No readable policy text was found in the PDF.")
    return {"pages": pages}


async def classify_node(state: GraphState) -> dict[str, list[dict[str, Any]]]:
    classifications = await classify_pages(state["pages"])
    if all(item.processing_status == "failed" for item in classifications):
        raise RuntimeError("Policy classification failed for every page.")
    supported = []
    page_numbers = {page.page_number for page in state["pages"]}
    for classification in classifications:
        if classification.page_number not in page_numbers:
            raise ValueError("The classifier returned a page outside the document.")
        supported.append(classification.model_dump(mode="json"))
    return {"classifications": supported}


def _upload_annotated_pdf(path: Path) -> str:
    if not all(
        (settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET)
    ):
        raise RuntimeError("Cloudinary is not configured in the OCR service.")
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )
    result = cloudinary.uploader.upload(
        str(path),
        resource_type="raw",
        type="authenticated",
        access_mode="authenticated",
        folder="bimalens/annotated",
        public_id=f"{uuid.uuid4().hex}_annotated.pdf",
        overwrite=False,
        unique_filename=False,
    )
    return str(result["public_id"])


async def annotate_node(state: GraphState) -> dict[str, Any]:
    source_path = Path(state["pdf_path"])
    output_path = Path(state["annotated_pdf_path"])
    serialized_pages = [page.model_dump(mode="json") for page in state["pages"]]
    annotation_summary = await asyncio.to_thread(
        annotate_pdf,
        source_path,
        output_path,
        state["pages"],
        state["classifications"],
    )
    public_id = await run_in_threadpool(_upload_annotated_pdf, output_path)

    with fitz.open(source_path) as document:
        page_count = document.page_count
    analysis_data = {
        "page_count": page_count,
        "pages": state["classifications"],
        "ocr": [
            {
                "page_number": page["page_number"],
                "method": page["method"],
                "confidence": page["confidence"],
            }
            for page in serialized_pages
        ],
        "annotations": annotation_summary["annotations"],
        "annotation_count": annotation_summary["annotation_count"],
    }
    return {
        "annotated_pdf_path": str(output_path),
        "annotated_pdf_public_id": public_id,
        "analysis_data": analysis_data,
    }


def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("download", download_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("annotate", annotate_node)
    workflow.add_edge(START, "download")
    workflow.add_edge("download", "extract")
    workflow.add_edge("extract", "classify")
    workflow.add_edge("classify", "annotate")
    workflow.add_edge("annotate", END)
    return workflow.compile()
