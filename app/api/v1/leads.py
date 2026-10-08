from datetime import datetime, timezone
from io import BytesIO
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from openpyxl import Workbook

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import require_roles
from app.db.session import get_db

from app.models.lead import Lead
from app.models.lead_extra_service import LeadExtraService
from app.models.lead_note import LeadNote
from app.models.notification import Notification
from app.models.user import User

from app.schemas.lead import (
    LeadAdminDetailResponse,
    LeadAdminListResponse,
    LeadAssignRequest,
    LeadCreate,
    LeadNoteCreate,
    LeadNoteResponse,
    LeadResponse,
    LeadStatusUpdate,
    LeadExtraServiceResponse,
    LeadManagerResponse,
    LeadNotificationResponse,
    LeadNoteAdminResponse,
)

from app.services.calculator import calculate_lead_price
from app.core.limiter import limiter


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)

@router.post(
    "",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
async def create_lead(
    request: Request,
    data: LeadCreate,
    db: AsyncSession = Depends(get_db),
):
    if not data.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is required",
        )

    now = datetime.now(timezone.utc)

    (
        final_price,
        base_price,
        discount,
        service_snapshots,
    ) = await calculate_lead_price(
        db=db,
        object_type=data.object_type,
        area=data.area,
        extra_service_ids=data.extra_service_ids,
    )

    lead = Lead(
        object_type=data.object_type,
        area=data.area,
        cleaning_frequency=data.cleaning_frequency,
        name=data.name,
        phone=data.phone,
        comment=data.comment,
        language=data.language,
        calculated_price=final_price,
        consent_given=True,
        consent_at=now,
        status="new",
        created_at=now,
        updated_at=now,
    )

    db.add(lead)

    await db.flush()

    for service, service_total in service_snapshots:
        lead_extra_service = LeadExtraService(
            lead_id=lead.id,
            extra_service_id=service.id,
            price_at_submission=service_total,
            created_at=now,
        )

        db.add(lead_extra_service)

    notification = Notification(
        lead_id=lead.id,
        type="telegram_lead",
        status="pending",
        attempts=0,
        next_attempt_at=now,
        created_at=now,
    )

    db.add(notification)

    await db.commit()

    await db.refresh(lead)

    return lead

    


@router.get(
    "/admin",
    response_model=LeadAdminListResponse,
)
async def get_admin_leads(
    search: str | None = None,
    status_filter: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "manager")
    ),
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than 0",
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100",
        )

    conditions = []

    if search:
        search_value = f"%{search.strip()}%"

        conditions.append(
            or_(
                Lead.name.ilike(search_value),
                Lead.phone.ilike(search_value),
            )
        )

    if status_filter:
        conditions.append(
            Lead.status == status_filter
        )

    if date_from:
        conditions.append(
            Lead.created_at >= date_from
        )

    if date_to:
        conditions.append(
            Lead.created_at <= date_to
        )

    total = await db.scalar(
        select(func.count(Lead.id)).where(
            *conditions
        )
    )

    offset = (page - 1) * page_size

    result = await db.scalars(
        select(Lead)
        .where(*conditions)
        .order_by(Lead.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    leads = list(result.all())

    pages = ceil(total / page_size) if total else 0

    return LeadAdminListResponse(
        items=leads,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )



@router.get(
    "/admin/{lead_id}",
    response_model=LeadAdminDetailResponse,
)
async def get_lead_admin_detail(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager")),
):
    result = await db.execute(
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.assigned_manager),
            selectinload(Lead.extra_services)
            .selectinload(LeadExtraService.extra_service),
            selectinload(Lead.notes)
            .selectinload(LeadNote.user),
            selectinload(Lead.notifications),
        )
    )

    lead = result.scalar_one_or_none()

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return LeadAdminDetailResponse(
        id=lead.id,

        object_type=lead.object_type,
        area=lead.area,
        cleaning_frequency=lead.cleaning_frequency,

        name=lead.name,
        phone=lead.phone,
        comment=lead.comment,
        language=lead.language,

        calculated_price=lead.calculated_price,

        consent_given=lead.consent_given,
        consent_at=lead.consent_at,

        status=lead.status,

        assigned_manager_id=lead.assigned_manager_id,

        assigned_manager=(
            LeadManagerResponse(
                id=lead.assigned_manager.id,
                username=lead.assigned_manager.username,
                role=lead.assigned_manager.role,
            )
            if lead.assigned_manager
            else None
        ),

        extra_services=[
            LeadExtraServiceResponse(
                id=item.id,
                extra_service_id=item.extra_service_id,
                price_at_submission=item.price_at_submission,
                service_name=item.extra_service.name,
            )
            for item in lead.extra_services
        ],

        notes=[
            LeadNoteAdminResponse(
                id=note.id,
                lead_id=note.lead_id,
                user_id=note.user_id,
                text=note.text,
                created_at=note.created_at,
                author_username=note.user.username,
            )
            for note in lead.notes
        ],

        notifications=[
            LeadNotificationResponse(
                id=notification.id,
                type=notification.type,
                status=notification.status,
                attempts=notification.attempts,
                error_message=notification.error_message,
                next_attempt_at=notification.next_attempt_at,
                sent_at=notification.sent_at,
                created_at=notification.created_at,
            )
            for notification in lead.notifications
        ],

        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


ALLOWED_LEAD_STATUSES = {
    "new",
    "called",
    "inspection_scheduled",
    "price_sent",
    "contract",
    "rejected",
}


@router.patch(
    "/admin/{lead_id}/status",
    response_model=LeadAdminDetailResponse,
)
async def update_lead_status(
    lead_id: int,
    data: LeadStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "manager")
    ),
):
    if data.status not in ALLOWED_LEAD_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. Allowed statuses: "
                "new, called, inspection_scheduled, "
                "price_sent, contract, rejected"
            ),
        )

    lead = await db.scalar(
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.assigned_manager),
            selectinload(Lead.extra_services)
            .selectinload(LeadExtraService.extra_service),
            selectinload(Lead.notes)
            .selectinload(LeadNote.user),
            selectinload(Lead.notifications),
        )
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    lead.status = data.status
    lead.updated_at = datetime.now(timezone.utc)

    await db.commit()

    await db.refresh(
        lead,
        attribute_names=[
            "assigned_manager",
            "extra_services",
            "notes",
            "notifications",
        ],
    )

    return LeadAdminDetailResponse(
        id=lead.id,

        object_type=lead.object_type,
        area=lead.area,
        cleaning_frequency=lead.cleaning_frequency,

        name=lead.name,
        phone=lead.phone,
        comment=lead.comment,
        language=lead.language,

        calculated_price=lead.calculated_price,

        consent_given=lead.consent_given,
        consent_at=lead.consent_at,

        status=lead.status,

        assigned_manager_id=lead.assigned_manager_id,

        assigned_manager=(
            LeadManagerResponse(
                id=lead.assigned_manager.id,
                username=lead.assigned_manager.username,
                role=lead.assigned_manager.role,
            )
            if lead.assigned_manager
            else None
        ),

        extra_services=[
            LeadExtraServiceResponse(
                id=item.id,
                extra_service_id=item.extra_service_id,
                price_at_submission=item.price_at_submission,
                service_name=item.extra_service.name,
            )
            for item in lead.extra_services
        ],

        notes=[
            LeadNoteAdminResponse(
                id=note.id,
                lead_id=note.lead_id,
                user_id=note.user_id,
                text=note.text,
                created_at=note.created_at,
                author_username=note.user.username,
            )
            for note in lead.notes
        ],

        notifications=[
            LeadNotificationResponse(
                id=notification.id,
                type=notification.type,
                status=notification.status,
                attempts=notification.attempts,
                error_message=notification.error_message,
                next_attempt_at=notification.next_attempt_at,
                sent_at=notification.sent_at,
                created_at=notification.created_at,
            )
            for notification in lead.notifications
        ],

        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.get(
    "/admin/{lead_id}/notes",
    response_model=list[LeadNoteResponse],
)
async def get_lead_notes(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "manager")
    ),
):
    lead_exists = await db.scalar(
        select(Lead.id).where(
            Lead.id == lead_id
        )
    )

    if not lead_exists:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    result = await db.scalars(
        select(LeadNote)
        .where(LeadNote.lead_id == lead_id)
        .order_by(LeadNote.created_at.desc())
    )

    return list(result.all())



@router.patch(
    "/admin/{lead_id}/assign",
    response_model=LeadAdminDetailResponse,
)
async def assign_lead_manager(
    lead_id: int,
    data: LeadAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "manager")
    ),
):
    lead = await db.scalar(
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.assigned_manager),
            selectinload(Lead.extra_services)
            .selectinload(LeadExtraService.extra_service),
            selectinload(Lead.notes)
            .selectinload(LeadNote.user),
            selectinload(Lead.notifications),
        )
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    if data.manager_id is None:
        lead.assigned_manager_id = None

    else:
        manager = await db.scalar(
            select(User).where(
                User.id == data.manager_id
            )
        )

        if not manager:
            raise HTTPException(
                status_code=404,
                detail="Manager not found",
            )

        if manager.role != "manager":
            raise HTTPException(
                status_code=400,
                detail="Selected user is not a manager",
            )

        if not manager.is_active:
            raise HTTPException(
                status_code=400,
                detail="Selected manager is inactive",
            )

        lead.assigned_manager_id = manager.id

    lead.updated_at = datetime.now(timezone.utc)

    await db.commit()

    await db.refresh(
        lead,
        attribute_names=[
            "assigned_manager",
            "extra_services",
            "notes",
            "notifications",
        ],
    )

    return LeadAdminDetailResponse(
        id=lead.id,

        object_type=lead.object_type,
        area=lead.area,
        cleaning_frequency=lead.cleaning_frequency,

        name=lead.name,
        phone=lead.phone,
        comment=lead.comment,
        language=lead.language,

        calculated_price=lead.calculated_price,

        consent_given=lead.consent_given,
        consent_at=lead.consent_at,

        status=lead.status,

        assigned_manager_id=lead.assigned_manager_id,

        assigned_manager=(
            LeadManagerResponse(
                id=lead.assigned_manager.id,
                username=lead.assigned_manager.username,
                role=lead.assigned_manager.role,
            )
            if lead.assigned_manager
            else None
        ),

        extra_services=[
            LeadExtraServiceResponse(
                id=item.id,
                extra_service_id=item.extra_service_id,
                price_at_submission=item.price_at_submission,
                service_name=item.extra_service.name,
            )
            for item in lead.extra_services
        ],

        notes=[
            LeadNoteAdminResponse(
                id=note.id,
                lead_id=note.lead_id,
                user_id=note.user_id,
                text=note.text,
                created_at=note.created_at,
                author_username=note.user.username,
            )
            for note in lead.notes
        ],

        notifications=[
            LeadNotificationResponse(
                id=notification.id,
                type=notification.type,
                status=notification.status,
                attempts=notification.attempts,
                error_message=notification.error_message,
                next_attempt_at=notification.next_attempt_at,
                sent_at=notification.sent_at,
                created_at=notification.created_at,
            )
            for notification in lead.notifications
        ],

        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.post(
    "/admin/{lead_id}/notes",
    response_model=LeadNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lead_note(
    lead_id: int,
    data: LeadNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "manager")
    ),
):
    lead = await db.scalar(
        select(Lead).where(
            Lead.id == lead_id
        )
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    now = datetime.now(timezone.utc)

    note = LeadNote(
        lead_id=lead.id,
        user_id=current_user.id,
        text=data.text,
        created_at=now,
    )

    db.add(note)

    lead.updated_at = now

    await db.commit()
    await db.refresh(note)

    return note


@router.get(
    "/admin/{lead_id}/notes",
    response_model=list[LeadNoteResponse],
)
async def get_lead_notes(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "manager")
    ),
):
    lead = await db.scalar(
        select(Lead).where(
            Lead.id == lead_id
        )
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    result = await db.scalars(
        select(LeadNote)
        .where(
            LeadNote.lead_id == lead_id
        )
        .order_by(
            LeadNote.created_at.desc()
        )
    )

    return list(result.all())




@router.get(
    "/export",
)
async def export_leads(
    search: str | None = None,
    status_filter: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "manager")
    ),
):
    conditions = []

    if search:
        search_value = f"%{search.strip()}%"

        conditions.append(
            or_(
                Lead.name.ilike(search_value),
                Lead.phone.ilike(search_value),
            )
        )

    if status_filter:
        conditions.append(
            Lead.status == status_filter
        )

    if date_from:
        conditions.append(
            Lead.created_at >= date_from
        )

    if date_to:
        conditions.append(
            Lead.created_at <= date_to
        )

    result = await db.scalars(
        select(Lead)
        .where(*conditions)
        .order_by(
            Lead.created_at.desc()
        )
    )

    leads = list(result.all())

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Leads"

    headers = [
        "ID",
        "Object Type",
        "Area (m²)",
        "Cleaning Frequency",
        "Name",
        "Phone",
        "Comment",
        "Language",
        "Calculated Price",
        "Consent",
        "Status",
        "Assigned Manager ID",
        "Created At",
        "Updated At",
    ]

    worksheet.append(headers)

    for lead in leads:
        worksheet.append(
            [
                lead.id,
                lead.object_type,
                float(lead.area),
                lead.cleaning_frequency,
                lead.name,
                lead.phone,
                lead.comment or "",
                lead.language,
                float(lead.calculated_price),
                "Yes" if lead.consent_given else "No",
                lead.status,
                lead.assigned_manager_id,
                lead.created_at.isoformat(),
                lead.updated_at.isoformat(),
            ]
        )

    column_widths = {
        "A": 10,
        "B": 20,
        "C": 15,
        "D": 22,
        "E": 20,
        "F": 20,
        "G": 40,
        "H": 12,
        "I": 20,
        "J": 12,
        "K": 25,
        "L": 20,
        "M": 30,
        "N": 30,
    }

    for column, width in column_widths.items():
        worksheet.column_dimensions[column].width = width

    worksheet.freeze_panes = "A2"

    file_stream = BytesIO()

    workbook.save(file_stream)

    file_stream.seek(0)

    return StreamingResponse(
        file_stream,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="leads.xlsx"'
            )
        },
    )