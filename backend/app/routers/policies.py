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
    PolicyUploadResponse,
)
from app.services import policy_service
from app.services.chat_service import ask_question, assess_fit

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
    annotated: bool = Query(default=True),
    owner_id: str = WorkspaceId,
):
    url = await policy_service.get_pdf_download_url(owner_id, policy_id, annotated)
    return PdfLinkResponse(url=url, expires_in=300)


@router.post("/{policy_id}/ask", response_model=AskResponse)
async def ask_policy_question(policy_id: str, body: AskRequest, owner_id: str = WorkspaceId):
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if policy["status"] != "ready":
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
    if policy["status"] != "ready":
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
    if policy["status"] != "ready":
        raise HTTPException(status_code=409, detail="Policy analysis is not ready yet.")
    return ClaimChecklistResponse(
        items=policy_service.claim_checklist(policy.get("analysis")),
        disclaimer="Checklist items summarize extracted policy clauses. They do not predict or guarantee a claim outcome.",
    )
