import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth import InternalService
from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo, get_db
from app.models.analysis import OcrCompleteWebhook
from app.routers import auth, chat, policies, pi_tools
from app.services.policy_service import complete_ocr

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="BimaLens API",
    description="Policy document storage, analysis, and source-grounded assistance.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-Internal-Token"],
)

app.include_router(policies.router)
app.include_router(chat.router)
app.include_router(pi_tools.router)
app.include_router(auth.router)


@app.post(
    "/api/v1/webhooks/ocr-complete",
    tags=["webhooks"],
    dependencies=[InternalService],
)
async def ocr_complete_webhook(payload: OcrCompleteWebhook):
    await complete_ocr(payload)
    return {"status": "ok"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "alive"}


@app.get("/ready", tags=["health"])
async def readiness_check():
    try:
        await get_db().command("ping")
    except Exception as error:
        logger.warning("Readiness check failed (%s).", type(error).__name__)
        raise HTTPException(status_code=503, detail="MongoDB is not ready.") from error
    return {"status": "ready"}
