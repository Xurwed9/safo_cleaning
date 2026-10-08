from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_roles
from app.db.session import get_db
from app.models.extra_service import ExtraService
from app.models.user import User
from app.schemas.extra_service import (
    ExtraServiceCreate,
    ExtraServiceResponse,
    ExtraServiceUpdate,
)
from sqlalchemy.orm import selectinload

from app.models.extra_service_translation import (
    ExtraServiceTranslation,
)

from app.schemas.extra_service import (
    ExtraServiceTranslationCreate,
    ExtraServiceTranslationResponse,
    SUPPORTED_LANGUAGES,
)


router = APIRouter(
    prefix="/extra-services",
    tags=["Extra Services"],
)


@router.get(
    "",
    response_model=list[ExtraServiceResponse],
)
async def get_extra_services(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(ExtraService)
        .where(ExtraService.is_active.is_(True))
        .order_by(ExtraService.name)
    )

    return list(result.all())


@router.post(
    "",
    response_model=ExtraServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_extra_service(
    data: ExtraServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner")
    ),
):
    existing = await db.scalar(
        select(ExtraService).where(
            ExtraService.code == data.code
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Extra service with this code already exists",
        )

    now = datetime.now(timezone.utc)

    service = ExtraService(
        code=data.code,
        name=data.name,
        price=data.price,
        pricing_type=data.pricing_type,
        is_active=data.is_active,
        created_at=now,
        updated_at=now,
    )

    db.add(service)

    await db.commit()
    await db.refresh(service)

    return service


@router.patch(
    "/{service_id}",
    response_model=ExtraServiceResponse,
)
async def update_extra_service(
    service_id: int,
    data: ExtraServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner")
    ),
):
    service = await db.scalar(
        select(ExtraService).where(
            ExtraService.id == service_id
        )
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extra service not found",
        )

    if data.code is not None:
        existing = await db.scalar(
            select(ExtraService).where(
                ExtraService.code == data.code,
                ExtraService.id != service_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Extra service with this code already exists",
            )

        service.code = data.code

    if data.name is not None:
        service.name = data.name

    if data.price is not None:
        service.price = data.price

    if data.pricing_type is not None:
        service.pricing_type = data.pricing_type

    if data.is_active is not None:
        service.is_active = data.is_active

    service.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(service)

    return service


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_extra_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner")
    ),
):
    service = await db.scalar(
        select(ExtraService).where(
            ExtraService.id == service_id
        )
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extra service not found",
        )

    service.is_active = False
    service.updated_at = datetime.now(timezone.utc)

    await db.commit()

    return None




@router.get(
    "",
    response_model=list[ExtraServiceResponse],
)
async def get_extra_services(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(ExtraService)
        .options(
            selectinload(
                ExtraService.translations
            )
        )
        .where(
            ExtraService.is_active.is_(True)
        )
        .order_by(
            ExtraService.id
        )
    )

    services = list(result.all())

    return services



@router.post(
    "/admin/{service_id}/translations",
    response_model=ExtraServiceTranslationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_extra_service_translation(
    service_id: int,
    data: ExtraServiceTranslationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "editor")
    ),
):
    if data.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported language",
        )

    service = await db.scalar(
        select(ExtraService).where(
            ExtraService.id == service_id
        )
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Extra service not found",
        )

    existing = await db.scalar(
        select(ExtraServiceTranslation).where(
            ExtraServiceTranslation.extra_service_id
            == service_id,
            ExtraServiceTranslation.language
            == data.language,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Translation already exists",
        )

    translation = ExtraServiceTranslation(
        extra_service_id=service_id,
        language=data.language,
        name=data.name,
        description=data.description,
    )

    db.add(translation)

    await db.commit()
    await db.refresh(translation)

    return translation



@router.patch(
    "/admin/translations/{translation_id}",
    response_model=ExtraServiceTranslationResponse,
)
async def update_extra_service_translation(
    translation_id: int,
    data: ExtraServiceTranslationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "editor")
    ),
):
    if data.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported language",
        )

    translation = await db.scalar(
        select(ExtraServiceTranslation).where(
            ExtraServiceTranslation.id
            == translation_id
        )
    )

    if not translation:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )

    duplicate = await db.scalar(
        select(ExtraServiceTranslation).where(
            ExtraServiceTranslation.extra_service_id
            == translation.extra_service_id,
            ExtraServiceTranslation.language
            == data.language,
            ExtraServiceTranslation.id
            != translation.id,
        )
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Translation already exists",
        )

    translation.language = data.language
    translation.name = data.name
    translation.description = data.description

    await db.commit()
    await db.refresh(translation)

    return translation