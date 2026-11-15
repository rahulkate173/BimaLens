from datetime import timedelta

from fastapi import Depends, HTTPException, Request, status
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import settings
SESSION_COOKIE = "bimalens_session"
SESSION_TTL_SECONDS = int(timedelta(days=14).total_seconds())


def _serializer() -> URLSafeTimedSerializer:
    if len(settings.SESSION_SECRET) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SESSION_SECRET must contain at least 32 characters.",
        )
    return URLSafeTimedSerializer(settings.SESSION_SECRET, salt="bimalens.workspace.v1")


def _check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in settings.cors_origins_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin is not allowed.")


def require_workspace(request: Request) -> str:
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        _check_origin(request)
    token = request.cookies.get(SESSION_COOKIE)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Workspace session required.")
    try:
        payload = _serializer().loads(token, max_age=SESSION_TTL_SECONDS)
    except BadSignature as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Workspace session expired."
        ) from error
    owner_id = payload.get("owner_id") if isinstance(payload, dict) else None
    if not isinstance(owner_id, str) or len(owner_id) != 32 or not owner_id.isalnum():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid workspace session.")
    return owner_id


def require_internal_token(
    request: Request,
) -> None:
    from app.services.ocr_client import verify_internal_token

    if not verify_internal_token(request.headers.get("X-Internal-Token")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Internal service token required.")


WorkspaceId = Depends(require_workspace)
InternalService = Depends(require_internal_token)
