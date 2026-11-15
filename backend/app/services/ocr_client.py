import hmac

import httpx

from app.config import settings


async def trigger_ocr_pipeline(policy_id: str, pdf_url: str) -> dict:
    if not settings.INTERNAL_API_TOKEN:
        raise RuntimeError("INTERNAL_API_TOKEN is not configured.")
    url = f"{settings.OCR_PIPELINE_URL.rstrip('/')}/api/v1/process"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            url,
            json={
                "policy_id": policy_id,
                "pdf_url": pdf_url,
            },
            headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
        )
        response.raise_for_status()
        return response.json()


def verify_internal_token(candidate: str | None) -> bool:
    return bool(settings.INTERNAL_API_TOKEN) and candidate is not None and hmac.compare_digest(
        candidate, settings.INTERNAL_API_TOKEN
    )
