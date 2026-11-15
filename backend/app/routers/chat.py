from fastapi import APIRouter, HTTPException

from app.auth import WorkspaceId
from app.models.policy import AskRequest, AskResponse
from app.services import policy_service
from app.services.chat_service import ask_question

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/{policy_id}", response_model=AskResponse, include_in_schema=False)
async def chat_with_policy(policy_id: str, body: AskRequest, owner_id: str = WorkspaceId):
    policy = await policy_service.get_policy(owner_id, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if policy["status"] != "ready":
        raise HTTPException(status_code=409, detail="Policy analysis is not ready yet.")
    return await ask_question(body.question, policy.get("analysis"), body.language)
