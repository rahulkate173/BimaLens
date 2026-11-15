import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> bool:
    global client, db
    if not settings.MONGODB_URI:
        logger.warning("MONGODB_URI is not configured; database routes will be unavailable.")
        return False

    client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        await client.admin.command("ping")
    except Exception:
        client.close()
        client = None
        logger.exception("Could not connect to MongoDB.")
        raise

    db = client[settings.MONGODB_DATABASE]
    await db.policies.create_index([("owner_id", 1), ("uploaded_at", -1)])
    await db.users.create_index("email", unique=True)
    logger.info("Connected to MongoDB database %s.", settings.MONGODB_DATABASE)
    return True


async def close_mongo_connection() -> None:
    global client, db
    if client is not None:
        client.close()
    client = None
    db = None


def get_db() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("MongoDB is not configured or available.")
    return db


def require_database() -> None:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not configured or available.",
        )
