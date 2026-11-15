import logging
import re
from datetime import datetime, timezone
from pathlib import PurePath
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app import cloudinary_client
from app.config import settings
from app.database import get_db
from app.models.analysis import OcrCompleteWebhook
from app.services.ocr_client import trigger_ocr_pipeline
from app.utils.helpers import serialize_doc, to_object_id

logger = logging.getLogger(__name__)
PDF_SIGNATURE = b"%PDF-"


def _filename(value: str | None) -> str:
    filename = PurePath(value or "policy.pdf").name
    safe = re.sub(r"[^A-Za-z0-9._ -]", "_", filename).strip(" .")
    if not safe.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    return safe[:180] or "policy.pdf"


def _public_policy(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None
    raw_status = document["status"]
    status = "ready" if raw_status == "completed" else raw_status
    return {
        "id": str(document["_id"]),
        "filename": document["filename"],
        "uploaded_at": document["uploaded_at"],
        "status": status,
        "error": document.get("error"),
        "analysis": document.get("analysis"),
    }


async def upload_policy(owner_id: str, file: UploadFile) -> dict[str, str]:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Upload a PDF document.")
    filename = _filename(file.filename)
    content = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="The PDF exceeds the 25 MB upload limit.")
    if not content.startswith(PDF_SIGNATURE):
        raise HTTPException(status_code=400, detail="The selected file is not a valid PDF.")

    try:
        asset = await run_in_threadpool(cloudinary_client.upload_pdf, content, filename)
    except Exception as error:
        logger.exception("Cloudinary upload failed.")
        raise HTTPException(status_code=502, detail="The PDF could not be stored. Check Cloudinary configuration.") from error

    db = get_db()
    document = {
        "owner_id": owner_id,
        "filename": filename,
        "cloudinary_public_id": asset["public_id"],
        "cloudinary_asset_id": asset["asset_id"],
        "uploaded_at": datetime.now(timezone.utc),
        "status": "processing",
        "analysis": None,
        "annotated_pdf_public_id": None,
        "error": None,
    }
    result = await db.policies.insert_one(document)
    policy_id = str(result.inserted_id)

    try:
        signed_pdf_url = await run_in_threadpool(
            cloudinary_client.create_download_url, asset["public_id"]
        )
        await trigger_ocr_pipeline(policy_id, signed_pdf_url)
    except Exception as error:
        logger.exception("Could not start OCR processing for policy %s.", policy_id)
        await db.policies.update_one(
            {"_id": result.inserted_id, "owner_id": owner_id},
            {"$set": {"status": "failed", "error": "Document processing could not be started."}},
        )
        return {"policy_id": policy_id, "status": "failed", "filename": filename}

    return {"policy_id": policy_id, "status": "processing", "filename": filename}


async def list_policies(owner_id: str) -> list[dict[str, Any]]:
    db = get_db()
    cursor = db.policies.find({"owner_id": owner_id}).sort("uploaded_at", -1)
    documents = await cursor.to_list(length=200)
    return [_public_policy(serialize_doc(document)) for document in documents]


async def get_policy(owner_id: str, policy_id: str) -> dict[str, Any] | None:
    try:
        object_id = to_object_id(policy_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    document = await get_db().policies.find_one({"_id": object_id, "owner_id": owner_id})
    return _public_policy(serialize_doc(document))


async def get_policy_for_service(policy_id: str) -> dict[str, Any] | None:
    try:
        object_id = to_object_id(policy_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    document = await get_db().policies.find_one({"_id": object_id})
    return _public_policy(serialize_doc(document))


async def get_policy_document(owner_id: str, policy_id: str) -> dict[str, Any] | None:
    try:
        object_id = to_object_id(policy_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return await get_db().policies.find_one({"_id": object_id, "owner_id": owner_id})


async def get_pdf_download_url(owner_id: str, policy_id: str, annotated: bool) -> str:
    document = await get_policy_document(owner_id, policy_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    public_id = document.get("annotated_pdf_public_id") if annotated else document.get("cloudinary_public_id")
    if not public_id:
        raise HTTPException(status_code=409, detail="The annotated PDF is not ready yet.")
    try:
        return await run_in_threadpool(cloudinary_client.create_download_url, public_id)
    except Exception as error:
        logger.exception("Could not create a PDF download link for policy %s.", policy_id)
        raise HTTPException(status_code=502, detail="A temporary PDF link could not be created.") from error


async def complete_ocr(payload: OcrCompleteWebhook) -> None:
    try:
        object_id: ObjectId = to_object_id(payload.policy_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Policy not found.") from error

    target_status = "ready" if payload.status == "completed" else payload.status
    fields: dict[str, Any] = {"status": target_status}
    if payload.status == "completed":
        if payload.analysis_data is None or payload.annotated_pdf_public_id is None:
            raise HTTPException(status_code=422, detail="Completed jobs must include analysis and an annotated PDF.")
        fields.update(
            analysis=payload.analysis_data,
            annotated_pdf_public_id=payload.annotated_pdf_public_id,
            error=None,
        )
    else:
        fields["error"] = payload.error or "Document analysis failed."

    result = await get_db().policies.update_one({"_id": object_id}, {"$set": fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found.")


def policy_sources(analysis: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not analysis:
        return []
    sources: list[dict[str, Any]] = []
    for page in analysis.get("pages", []):
        page_number = page.get("page_number")
        if not isinstance(page_number, int):
            continue
        section = page.get("section_title") or ""
        for point in page.get("extracted_points", []):
            quote = point.get("exact_quote")
            if not isinstance(quote, str) or not quote.strip():
                continue
            sources.append(
                {
                    "page": page_number,
                    "section": section,
                    "quote": quote,
                    "category": point.get("category", "Metadata"),
                    "point_summary": point.get("point_summary", ""),
                }
            )
    return sources


def claim_checklist(analysis: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [
        item
        for item in policy_sources(analysis)
        if item["category"] in {"Obligation", "Red_Flag"}
    ]
