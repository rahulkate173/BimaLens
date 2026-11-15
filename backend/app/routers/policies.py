import os

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.auth import WorkspaceId
from app.database import require_database
from app.models.policy import (
    AskRequest,
    AskResponse,
    ClaimChecklistResponse,
    FitRequest,
    FitResponse,
    PdfLinkResponse,
    PolicySummaryResponse,
    PolicyUploadResponse,
    TTSRequest,
    TTSResponse,
)
from app.services import policy_service, rag_store
from app.services.chat_service import ask_question, assess_fit, generate_summary

router = APIRouter(
    prefix="/api/v1/policies",
    tags=["policies"],
    dependencies=[Depends(require_database)],
)


@router.post("/upload", response_model=PolicyUploadResponse, status_code=202)
async def upload_policy(file: UploadFile = File(...), owner_id: str = WorkspaceId):
    result = await policy_service.upload_policy(owner_id, file)
    if result["status"] == "failed":
        raise HTTPException(
            status_code=502,
            detail={"message": "Policy was stored, but document analysis could not be started.", **result},
        )
    return result


@router.get("")
async def list_policies(owner_id: str = WorkspaceId):
    try:
        return await policy_service.list_policies(owner_id)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/{policy_id}")
async def get_policy(policy_id: str, owner_id: str = WorkspaceId):
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    return policy


@router.get("/{policy_id}/analysis")
async def get_analysis(policy_id: str, owner_id: str = WorkspaceId):
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if policy["status"] == "processing":
        raise HTTPException(status_code=409, detail="Policy analysis is still processing.")
    if policy["status"] == "failed":
        raise HTTPException(status_code=422, detail=policy.get("error") or "Policy analysis failed.")
    return policy.get("analysis") or {}


@router.get("/{policy_id}/status")
async def get_status(policy_id: str, owner_id: str = WorkspaceId):
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    return {
        "policy_id": policy_id,
        "status": policy["status"],
        "filename": policy["filename"],
        "error": policy.get("error"),
    }


@router.get("/{policy_id}/pdf-link", response_model=PdfLinkResponse)
async def get_pdf_link(
    policy_id: str,
    owner_id: str = WorkspaceId,
):
    url = await policy_service.get_pdf_download_url(owner_id, policy_id)
    return PdfLinkResponse(url=url, expires_in=300)


@router.post("/{policy_id}/ask", response_model=AskResponse)
async def ask_policy_question(policy_id: str, body: AskRequest, owner_id: str = WorkspaceId):
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if policy["status"] not in ("ready", "completed"):
        raise HTTPException(status_code=409, detail="Policy analysis is not ready yet.")
    result = await ask_question(
        question=body.question,
        analysis_data=policy.get("analysis"),
        language=body.language,
    )
    return result


@router.post("/{policy_id}/fit", response_model=FitResponse)
async def check_policy_fit(policy_id: str, body: FitRequest, owner_id: str = WorkspaceId):
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if policy["status"] not in ("ready", "completed"):
        raise HTTPException(status_code=409, detail="Policy analysis is not ready yet.")
    result = await assess_fit(
        profile=body.model_dump(exclude_none=True),
        analysis_data=policy.get("analysis"),
    )
    return FitResponse(
        summary=result["answer"],
        observations=result["sources"],
        limitations=[
            "This is a document-grounded comparison, not a financial or insurance recommendation.",
            "The policy may not contain enough information to determine suitability for your needs.",
        ],
        provider=result["provider"],
    )


@router.get("/{policy_id}/claims", response_model=ClaimChecklistResponse)
async def get_claim_checklist(policy_id: str, owner_id: str = WorkspaceId):
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if policy["status"] not in ("ready", "completed"):
        raise HTTPException(status_code=409, detail="Policy analysis is not ready yet.")
    return ClaimChecklistResponse(
        items=policy_service.claim_checklist(policy.get("analysis")),
        disclaimer="Checklist items summarize extracted policy clauses. They do not predict or guarantee a claim outcome.",
    )


@router.get("/{policy_id}/summary", response_model=PolicySummaryResponse)
async def get_policy_summary(
    policy_id: str,
    language: str = Query(default="English", min_length=2, max_length=30),
    owner_id: str = WorkspaceId,
):
    """Generate a critical-points summary of the policy, then cache chunks in SQLite."""
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if policy["status"] not in ("ready", "completed"):
        raise HTTPException(status_code=409, detail="Policy analysis is not ready yet.")

    # Populate / refresh the SQLite RAG store for this policy
    sources = policy_service.policy_sources(policy.get("analysis"))
    if sources:
        rag_store.store_policy_chunks(policy_id, sources)

    result = await generate_summary(policy.get("analysis"), language=language)
    return PolicySummaryResponse(
        summary=result["summary"],
        language=language,
        provider=result.get("provider"),
    )


@router.post("/{policy_id}/tts", response_model=TTSResponse)
async def text_to_speech(
    policy_id: str,
    body: TTSRequest,
    owner_id: str = WorkspaceId,
):
    """Convert text to speech via Sarvam AI TTS (bulbul:v3)."""
    # Confirm policy belongs to this user
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")

    sarvam_key = os.environ.get("SARVAM_API_KEY", "")
    if not sarvam_key:
        raise HTTPException(status_code=503, detail="Sarvam API key is not configured.")

    language_codes = {
        "en": "en-IN",
        "english": "en-IN",
        "en-in": "en-IN",
        "hi": "hi-IN",
        "hindi": "hi-IN",
        "hi-in": "hi-IN",
    }
    target_language_code = language_codes.get(body.language.casefold(), body.language)

    # Sarvam TTS supports max ~500 chars per input; chunk the text
    text_chunks = [body.text[i:i + 500] for i in range(0, len(body.text), 500)]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            audio_parts: list[str] = []
            for chunk in text_chunks[:10]:  # cap at ~5000 chars
                response = await client.post(
                    "https://api.sarvam.ai/text-to-speech",
                    headers={
                        "Authorization": f"Bearer {sarvam_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "inputs": [chunk],
                        "target_language_code": target_language_code,
                        "speaker": "priya",
                        "model": "bulbul:v3",
                        "enable_preprocessing": True,
                    },
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Sarvam TTS returned {response.status_code}: {response.text[:1000]}",
                    )
                data = response.json()
                audios = data.get("audios") or []
                if audios:
                    audio_parts.append(audios[0])

        if not audio_parts:
            raise HTTPException(status_code=502, detail="Sarvam TTS returned no audio data.")

        return TTSResponse(audio_base64=audio_parts[0], audio_chunks=audio_parts)

    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Sarvam TTS request timed out.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"TTS request failed: {exc}") from exc
