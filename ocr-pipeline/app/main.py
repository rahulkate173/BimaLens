import hmac
import logging
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from app.config import settings
from app.models.schemas import JobStatus, ProcessRequest, ProcessResponse
from app.pipeline.document import validate_cloudinary_url

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.queue = None
    try:
        app.state.queue = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        logger.info("Connected to the OCR Redis queue.")
    except Exception as error:
        logger.error("OCR Redis queue is unavailable (%s).", type(error).__name__)
    yield
    queue: ArqRedis | None = app.state.queue
    if queue is not None:
        await queue.close()


app = FastAPI(
    title="BimaLens OCR Pipeline",
    description="Queued OCR, clause classification, and annotated policy PDF processing.",
    version="1.0.0",
    lifespan=lifespan,
)


async def require_internal_token(
    request: Request,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> None:
    if (
        not settings.INTERNAL_API_TOKEN
        or x_internal_token is None
        or not hmac.compare_digest(x_internal_token, settings.INTERNAL_API_TOKEN)
    ):
        raise HTTPException(status_code=401, detail="Internal service token required.")


@app.post(
    "/api/v1/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_internal_token)],
)
async def start_processing(body: ProcessRequest, request: Request):
    try:
        validate_cloudinary_url(str(body.pdf_url))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    queue: ArqRedis | None = request.app.state.queue
    if queue is None:
        raise HTTPException(status_code=503, detail="The document processing queue is unavailable.")

    job_id = __import__("uuid").uuid4().hex
    payload = {
        "job_id": job_id,
        "policy_id": body.policy_id,
        "pdf_url": str(body.pdf_url),
    }
    try:
        await queue.enqueue_job(
            "process_policy",
            payload,
            _job_id=f"ocr-{job_id}",
            _queue_name=settings.OCR_QUEUE_NAME,
        )
    except Exception as error:
        logger.exception("Could not enqueue an OCR job.")
        raise HTTPException(status_code=503, detail="The document processing job could not be queued.") from error

    return ProcessResponse(status=JobStatus.ACCEPTED, job_id=job_id)


@app.get("/health")
async def health_check():
    return {"status": "alive"}


@app.get("/ready")
async def readiness_check(request: Request):
    queue: ArqRedis | None = request.app.state.queue
    if queue is None:
        raise HTTPException(status_code=503, detail="The OCR queue is not ready.")
    try:
        await queue.ping()
    except Exception as error:
        raise HTTPException(status_code=503, detail="The OCR queue is not ready.") from error
    return {"status": "ready"}
