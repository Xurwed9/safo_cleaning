from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.analytics_event import AnalyticsEvent
from app.schemas.analytics import (
    ALLOWED_EVENT_TYPES,
    AnalyticsEventCreate,
)

router = APIRouter(
    prefix="/events",
    tags=["Analytics"],
)


@router.post("")
async def create_event(
    data: AnalyticsEventCreate,
    db: AsyncSession = Depends(get_db),
):
    if data.event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported event type",
        )

    event = AnalyticsEvent(
        event_type=data.event_type,
        lead_id=data.lead_id,
        event_metadata=data.metadata,
        created_at=datetime.now(timezone.utc),
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    return {
        "message": "Event recorded",
        "id": event.id,
    }