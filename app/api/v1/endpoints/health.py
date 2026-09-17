from fastapi import APIRouter, HTTPException, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.core.redis import redis_client
from app.db.session import AsyncSessionLocal

router = APIRouter()


@router.get("/live", tags=["Health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", tags=["Health"])
async def readiness() -> dict[str, str]:
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        await redis_client.ping()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies are not ready.",
        ) from exc

    return {"status": "ready"}


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
