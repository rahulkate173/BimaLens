"""ARQ task used by the standalone OCR worker process."""

import logging
import tempfile
from pathlib import Path
from typing import Any

import httpx
from arq.worker import Retry

from app.config import settings
from app.models.schemas import CallbackPayload
from app.pipeline.graph import build_graph

logger = logging.getLogger(__name__)
MAX_JOB_TRIES = 3


async def _notify_backend(callback: CallbackPayload) -> None:
    if not settings.INTERNAL_API_TOKEN:
        raise RuntimeError("INTERNAL_API_TOKEN is not configured.")
    url = f"{settings.BACKEND_CALLBACK_URL.rstrip('/')}/api/v1/webhooks/ocr-complete"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            json=callback.model_dump(mode="json"),
            headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
        )
        response.raise_for_status()


async def process_policy(ctx: dict[str, Any], payload: dict[str, str]) -> None:
    job_id = payload["job_id"]
    policy_id = payload["policy_id"]
    logger.info("Starting OCR job %s for policy %s.", job_id, policy_id)
    try:
        with tempfile.TemporaryDirectory(prefix="bimalens-") as directory:
            source = Path(directory) / "policy.pdf"
            annotated = Path(directory) / "annotated.pdf"
            result = await build_graph().ainvoke(
                {
                    "job_id": job_id,
                    "policy_id": policy_id,
                    "pdf_url": payload["pdf_url"],
                    "pdf_path": str(source),
                    "annotated_pdf_path": str(annotated),
                }
            )
        callback = CallbackPayload(
            job_id=job_id,
            policy_id=policy_id,
            status="completed",
            analysis_data=result["analysis_data"],
            annotated_pdf_public_id=result["annotated_pdf_public_id"],
        )
        await _notify_backend(callback)
        logger.info("OCR job %s completed.", job_id)
    except Exception:
        logger.exception("OCR job %s failed.", job_id)
        if ctx.get("job_try", 1) >= MAX_JOB_TRIES:
            try:
                await _notify_backend(
                    CallbackPayload(
                        job_id=job_id,
                        policy_id=policy_id,
                        status="failed",
                        error="Policy processing failed. Check the service configuration or upload the document again.",
                    )
                )
            except Exception:
                logger.exception("Could not send failed-job callback for %s.", job_id)
        else:
            logger.warning(
                "OCR job %s will be retried (attempt %s of %s).",
                job_id,
                ctx.get("job_try", 1),
                MAX_JOB_TRIES,
            )
            raise Retry(defer=10)
        raise


class WorkerSettings:
    from arq.connections import RedisSettings

    functions = [process_policy]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    queue_name = settings.OCR_QUEUE_NAME
    max_jobs = 2
    job_timeout = 60 * 60
    max_tries = MAX_JOB_TRIES
