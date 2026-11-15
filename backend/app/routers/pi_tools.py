from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_internal_token
from app.database import require_database
from app.models.analysis import ClauseToolRequest
from app.services import policy_service

router = APIRouter(
    prefix="/api/v1/pi",
    tags=["Paytm Pi tools"],
    dependencies=[Depends(require_database)],
)
TOOLS = {
    "get_coverage": {"description": "Return coverage and financial clauses with source references."},
    "check_exclusion": {"description": "Return exclusion and red-flag clauses with source references."},
    "find_gaps": {"description": "Return policy facts relevant to a supplied question; do not infer missing coverage."},
    "claim_readiness": {"description": "Return obligations and deadlines extracted from the policy."},
}


@router.get("/manifest")
async def get_tool_manifest(_: None = Depends(require_internal_token)):
    return {
        "name": "BimaLens Policy Graph",
        "version": "1.0",
        "tools": [{"name": name, **details} for name, details in TOOLS.items()],
        "integration_status": "tool-contract-only",
    }


@router.post("/tools/{tool_name}")
async def invoke_pi_tool(
    tool_name: str,
    body: ClauseToolRequest,
    _: None = Depends(require_internal_token),
):
    if tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail="Unknown BimaLens tool.")
    policy = await policy_service.get_policy_for_service(body.policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if policy["status"] != "ready":
        raise HTTPException(status_code=409, detail="Policy analysis is not ready yet.")

    sources = policy_service.policy_sources(policy.get("analysis"))
    if tool_name == "get_coverage":
        selected = [item for item in sources if item["category"] in {"Coverage", "Financial"}]
    elif tool_name == "check_exclusion":
        selected = [item for item in sources if item["category"] in {"Exclusion", "Red_Flag"}]
    elif tool_name == "claim_readiness":
        selected = policy_service.claim_checklist(policy.get("analysis"))
    else:
        if not body.question:
            raise HTTPException(status_code=422, detail="A question is required for find_gaps.")
        from app.services.chat_service import rank_sources

        selected = rank_sources(body.question, sources)

    return {
        "policy_id": body.policy_id,
        "tool": tool_name,
        "findings": selected,
        "notice": "Only source-backed policy clauses are returned; absence of a clause is not evidence of coverage.",
    }
