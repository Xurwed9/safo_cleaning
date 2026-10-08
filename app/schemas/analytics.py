from datetime import datetime

from pydantic import BaseModel, Field


ALLOWED_EVENT_TYPES = {
    "phone_click",
    "whatsapp_click",
    "telegram_click",
}


class AnalyticsEventCreate(BaseModel):
    event_type: str = Field(
        min_length=1,
        max_length=50,
    )

    lead_id: int | None = None

    metadata: dict | None = None


class AnalyticsEventResponse(BaseModel):
    id: int
    event_type: str
    lead_id: int | None
    metadata: dict | None
    created_at: datetime