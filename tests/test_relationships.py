import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.extra_service import ExtraService
from app.models.lead import Lead
from app.models.lead_extra_service import LeadExtraService
from app.models.lead_note import LeadNote
from app.models.user import User


async def create_test_user(db):
    now = datetime.now(timezone.utc)

    user = User(
        username=f"relationship_test_{uuid.uuid4().hex[:8]}",
        password_hash="test_hash",
        role="manager",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db.add(user)
    await db.flush()

    return user


async def create_test_lead(db):
    now = datetime.now(timezone.utc)

    lead = Lead(
        object_type="office",
        area=Decimal("100.00"),
        cleaning_frequency="weekly",
        name=f"Relationship Test {uuid.uuid4().hex[:8]}",
        phone=f"+992900{uuid.uuid4().int % 1000000:06d}",
        comment=None,
        language="ru",
        calculated_price=Decimal("1000.00"),
        consent_given=True,
        consent_at=now,
        status="new",
        assigned_manager_id=None,
        created_at=now,
        updated_at=now,
    )

    db.add(lead)
    await db.flush()

    return lead


async def test_user_lead_relationship():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db)
        lead = await create_test_lead(db)

        lead.assigned_manager_id = user.id

        await db.flush()

        result = await db.scalar(
            select(Lead).where(
                Lead.id == lead.id
            )
        )

        assert result is not None
        assert result.assigned_manager_id == user.id

        await db.rollback()


async def test_lead_note_relationship():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db)
        lead = await create_test_lead(db)

        note = LeadNote(
            lead_id=lead.id,
            user_id=user.id,
            text="Relationship test note",
            created_at=datetime.now(timezone.utc),
        )

        db.add(note)

        await db.flush()

        result = await db.scalar(
            select(LeadNote).where(
                LeadNote.id == note.id
            )
        )

        assert result is not None
        assert result.lead_id == lead.id
        assert result.user_id == user.id

        await db.rollback()


async def test_lead_extra_service_relationship():
    async with AsyncSessionLocal() as db:
        lead = await create_test_lead(db)

        service = ExtraService(
            code=f"relationship_test_{uuid.uuid4().hex[:8]}",
            name="Relationship Test Service",
            price=Decimal("100.00"),
            pricing_type="fixed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(service)

        await db.flush()

        lead_service = LeadExtraService(
            lead_id=lead.id,
            extra_service_id=service.id,
            price_at_submission=Decimal("100.00"),
            created_at=datetime.now(timezone.utc),
        )

        db.add(lead_service)

        await db.flush()

        result = await db.scalar(
            select(LeadExtraService).where(
                LeadExtraService.id == lead_service.id
            )
        )

        assert result is not None
        assert result.lead_id == lead.id
        assert result.extra_service_id == service.id

        await db.rollback()