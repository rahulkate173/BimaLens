from datetime import datetime, timedelta, timezone
from io import BytesIO
from uuid import uuid4

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from app.config import settings


def configure_cloudinary() -> None:
    if not all(
        (settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET)
    ):
        raise RuntimeError("Cloudinary is not configured.")
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_pdf(file_bytes: bytes, filename: str, *, folder: str = "policies") -> dict[str, str]:
    """Store a PDF as an authenticated raw asset with an unguessable public ID."""
    configure_cloudinary()
    result = cloudinary.uploader.upload(
        BytesIO(file_bytes),
        resource_type="raw",
        type="authenticated",
        access_mode="authenticated",
        folder=f"bimalens/{folder}",
        public_id=f"{uuid4().hex}_{filename}",
        overwrite=False,
        unique_filename=False,
    )
    return {"public_id": result["public_id"], "asset_id": result["asset_id"]}


def create_download_url(public_id: str, *, expires_in: int = 300) -> str:
    """Create a short-lived URL for an authenticated raw PDF."""
    configure_cloudinary()
    expires_at = int((datetime.now(timezone.utc) + timedelta(seconds=expires_in)).timestamp())
    return cloudinary.utils.private_download_url(
        public_id,
        format="pdf",
        resource_type="raw",
        type="authenticated",
        expires_at=expires_at,
    )
