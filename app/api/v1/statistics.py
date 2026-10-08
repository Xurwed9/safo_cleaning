from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_roles
from app.db.session import get_db
from app.models.analytics_event import AnalyticsEvent
from app.models.lead import Lead
from app.schemas.statistics import StatisticsResponse

router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)

def get_period_start(
    period: str,
) -> datetime:
    now = datetime.now(timezone.utc)

    if period == "day":
        return now - timedelta(days=1)

    if period == "week":
        return now - timedelta(days=7)

    if period == "month":
        return now - timedelta(days=30)

    raise ValueError("Invalid period")



@router.get(
    "",
    response_model=StatisticsResponse,
    dependencies=[
        Depends(
            require_roles(
                "owner",
                "manager",
            )
        )
    ],
)
async def get_statistics(
    period: str = "day",
    db: AsyncSession = Depends(get_db),
):
    start = get_period_start(period)

    leads = await db.scalar(
        select(
            func.count(Lead.id)
        ).where(
            Lead.created_at >= start
        )
    )

    contracts = await db.scalar(
        select(
            func.count(Lead.id)
        ).where(
            Lead.status == "contract",
            Lead.updated_at >= start,
        )
    )

    phone_clicks = await db.scalar(
        select(
            func.count(AnalyticsEvent.id)
        ).where(
            AnalyticsEvent.event_type
            == "phone_click",
            AnalyticsEvent.created_at >= start,
        )
    )

    whatsapp_clicks = await db.scalar(
        select(
            func.count(AnalyticsEvent.id)
        ).where(
            AnalyticsEvent.event_type
            == "whatsapp_click",
            AnalyticsEvent.created_at >= start,
        )
    )

    telegram_clicks = await db.scalar(
        select(
            func.count(AnalyticsEvent.id)
        ).where(
            AnalyticsEvent.event_type
            == "telegram_click",
            AnalyticsEvent.created_at >= start,
        )
    )

    return StatisticsResponse(
        period=period,
        leads=leads or 0,
        contracts=contracts or 0,
        phone_clicks=phone_clicks or 0,
        whatsapp_clicks=whatsapp_clicks or 0,
        telegram_clicks=telegram_clicks or 0,
    )