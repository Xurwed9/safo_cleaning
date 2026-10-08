from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.lead import Lead
from app.models.lead_extra_service import LeadExtraService
from app.models.extra_service import ExtraService

from app.services.telegram import (
    send_telegram_message,
    build_lead_message,
    build_whatsapp_button,
)


MAX_NOTIFICATION_ATTEMPTS = 5


def get_retry_delay(attempt: int) -> timedelta:
    delays = {
        1: timedelta(seconds=30),
        2: timedelta(minutes=1),
        3: timedelta(minutes=5),
        4: timedelta(minutes=15),
    }

    return delays.get(
        attempt,
        timedelta(hours=1),
    )


async def send_lead_notification(
    db: AsyncSession,
    notification: Notification,
) -> bool:

    lead = await db.scalar(
        select(Lead).where(
            Lead.id == notification.lead_id
        )
    )

    if not lead:
        notification.status = "failed"
        notification.error_message = "Lead not found"
        notification.attempts += 1
        notification.next_attempt_at = None

        await db.commit()

        return False

    result = await db.scalars(
        select(ExtraService)
        .join(
            LeadExtraService,
            LeadExtraService.extra_service_id == ExtraService.id,
        )
        .where(
            LeadExtraService.lead_id == lead.id
        )
    )

    extra_services = list(result.all())

    extra_service_names = [
        service.name
        for service in extra_services
    ]

    telegram_message = build_lead_message(
        object_type=lead.object_type,
        area=lead.area,
        cleaning_frequency=lead.cleaning_frequency,
        name=lead.name,
        phone=lead.phone,
        language=lead.language,
        calculated_price=lead.calculated_price,
        comment=lead.comment,
        extra_services=extra_service_names,
    )

    telegram_button = build_whatsapp_button(
        lead.phone
    )

    notification.attempts += 1

    try:
        await send_telegram_message(
            text=telegram_message,
            reply_markup=telegram_button,
        )

        notification.status = "sent"
        notification.sent_at = datetime.now(timezone.utc)
        notification.error_message = None
        notification.next_attempt_at = None

        await db.commit()

        return True

    except Exception as exc:
        notification.status = "failed"
        notification.error_message = str(exc)

        if notification.attempts >= MAX_NOTIFICATION_ATTEMPTS:
            notification.next_attempt_at = None
        else:
            notification.next_attempt_at = (
                datetime.now(timezone.utc)
                + get_retry_delay(notification.attempts)
            )

        await db.commit()

        return False


