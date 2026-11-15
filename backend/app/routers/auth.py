import logging
import re
from datetime import datetime, timezone
from hashlib import pbkdf2_hmac
from secrets import compare_digest, token_bytes
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pymongo.errors import DuplicateKeyError

from app.auth import SESSION_COOKIE, SESSION_TTL_SECONDS, WorkspaceId, _check_origin, _serializer
from app.config import settings
from app.database import get_db, require_database
from app.models.account import (
    AccountResponse,
    AccountUpdateRequest,
    LoginRequest,
    NotificationPreferences,
    SignUpRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"], dependencies=[Depends(require_database)])
PASSWORD_ITERATIONS = 310_000
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    return normalized


def _hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        iterations, salt_hex, digest_hex = stored_hash.split("$", 2)
        candidate = pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        ).hex()
        return compare_digest(candidate, digest_hex)
    except (ValueError, TypeError):
        return False


def _account_response(account: dict) -> AccountResponse:
    preferences = account.get("notifications") or {}
    return AccountResponse(
        id=str(account["_id"]),
        name=account["name"],
        email=account["email"],
        notifications=NotificationPreferences(
            policy_updates=preferences.get("policy_updates", True),
            product_updates=preferences.get("product_updates", False),
        ),
    )


def _start_account_session(response: Response, request: Request, owner_id: str) -> None:
    _check_origin(request)
    secure_cookie = settings.SESSION_COOKIE_SECURE
    response.set_cookie(
        key=SESSION_COOKIE,
        value=_serializer().dumps({"owner_id": owner_id}),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=secure_cookie,
        samesite="none" if secure_cookie else "lax",
        path="/",
    )


@router.post("/signup", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignUpRequest, request: Request, response: Response):
    _check_origin(request)
    _serializer()
    email = _normalize_email(body.email)
    name = body.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Name must contain at least 2 characters.")
    owner_id = uuid4().hex
    account = {
        "_id": owner_id,
        "name": name,
        "email": email,
        "password_hash": _hash_password(body.password),
        "notifications": {"policy_updates": True, "product_updates": False},
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await get_db().users.insert_one(account)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from error
    _start_account_session(response, request, owner_id)
    logger.info("Account created (account_id=%s).", owner_id)
    return _account_response(account)


@router.post("/login", response_model=AccountResponse)
async def login(body: LoginRequest, request: Request, response: Response):
    _check_origin(request)
    email = _normalize_email(body.email)
    account = await get_db().users.find_one({"email": email})
    if account is None or not _verify_password(body.password, account.get("password_hash", "")):
        logger.info("Rejected sign-in attempt.")
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    _start_account_session(response, request, str(account["_id"]))
    logger.info("Account signed in (account_id=%s).", account["_id"])
    return _account_response(account)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    _check_origin(request)
    secure_cookie = settings.SESSION_COOKIE_SECURE
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        secure=secure_cookie,
        samesite="none" if secure_cookie else "lax",
    )
    logger.info("Account session ended.")


@router.get("/me", response_model=AccountResponse)
async def get_account(owner_id: str = WorkspaceId):
    account = await get_db().users.find_one({"_id": owner_id})
    if account is None:
        raise HTTPException(status_code=401, detail="Account no longer exists.")
    return _account_response(account)


@router.patch("/me", response_model=AccountResponse)
async def update_account(body: AccountUpdateRequest, owner_id: str = WorkspaceId):
    name = body.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Name must contain at least 2 characters.")
    account = await get_db().users.find_one_and_update(
        {"_id": owner_id}, {"$set": {"name": name}}, return_document=True
    )
    if account is None:
        raise HTTPException(status_code=401, detail="Account no longer exists.")
    logger.info("Account profile updated (account_id=%s).", owner_id)
    return _account_response(account)


@router.patch("/notifications", response_model=AccountResponse)
async def update_notifications(
    preferences: NotificationPreferences, owner_id: str = WorkspaceId
):
    account = await get_db().users.find_one_and_update(
        {"_id": owner_id},
        {"$set": {"notifications": preferences.model_dump()}},
        return_document=True,
    )
    if account is None:
        raise HTTPException(status_code=401, detail="Account no longer exists.")
    logger.info("Notification preferences updated (account_id=%s).", owner_id)
    return _account_response(account)
