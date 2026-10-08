from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_roles
from app.db.session import get_db
from app.models.pricing import Pricing
from app.models.user import User
from app.schemas.pricing import (
    PricingCalculateRequest,
    PricingCalculateResponse,
    PricingCreate,
    PricingResponse,
    PricingUpdate,
)
from app.services.calculator import calculate_lead_price
from decimal import Decimal

router = APIRouter(
    prefix="/pricing",
    tags=["Pricing"],
)


@router.get(
    "",
    response_model=list[PricingResponse],
)
async def get_pricing(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Pricing)
        .where(Pricing.is_active.is_(True))
        .order_by(Pricing.object_type)
    )

    return list(result.all())


@router.post(
    "",
    response_model=PricingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pricing(
    data: PricingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner")
    ),
):
    existing = await db.scalar(
        select(Pricing).where(
            Pricing.object_type == data.object_type
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pricing for this object type already exists",
        )

    now = datetime.now(timezone.utc)

    pricing = Pricing(
        object_type=data.object_type,
        price_per_m2=data.price_per_m2,
        minimum_order=data.minimum_order,
        discount_threshold_m2=data.discount_threshold_m2,
        discount_percent=data.discount_percent,
        is_active=data.is_active,
        created_at=now,
        updated_at=now,
    )

    db.add(pricing)

    await db.commit()
    await db.refresh(pricing)

    return pricing


@router.patch(
    "/{pricing_id}",
    response_model=PricingResponse,
)
async def update_pricing(
    pricing_id: int,
    data: PricingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner")
    ),
):
    pricing = await db.scalar(
        select(Pricing).where(
            Pricing.id == pricing_id
        )
    )

    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing not found",
        )

    if data.object_type is not None:
        existing = await db.scalar(
            select(Pricing).where(
                Pricing.object_type == data.object_type,
                Pricing.id != pricing_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pricing for this object type already exists",
            )

        pricing.object_type = data.object_type

    if data.price_per_m2 is not None:
        pricing.price_per_m2 = data.price_per_m2

    if data.minimum_order is not None:
        pricing.minimum_order = data.minimum_order

    if data.discount_threshold_m2 is not None:
        pricing.discount_threshold_m2 = (
            data.discount_threshold_m2
        )

    if data.discount_percent is not None:
        pricing.discount_percent = data.discount_percent

    if data.is_active is not None:
        pricing.is_active = data.is_active

    pricing.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(pricing)

    return pricing


@router.delete(
    "/{pricing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pricing(
    pricing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner")
    ),
):
    pricing = await db.scalar(
        select(Pricing).where(
            Pricing.id == pricing_id
        )
    )

    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing not found",
        )

    pricing.is_active = False
    pricing.updated_at = datetime.now(timezone.utc)

    await db.commit()

    return None



@router.post(
    "/calculate",
    response_model=PricingCalculateResponse,
)
async def calculate_price(
    data: PricingCalculateRequest,
    db: AsyncSession = Depends(get_db),
):
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

    extra_services_price = sum(
        (
            service_total
            for _, service_total in service_snapshots
        ),
        Decimal("0"),
    )

    return PricingCalculateResponse(
        object_type=data.object_type,
        area=data.area,
        base_price=base_price,
        discount=discount,
        extra_services_price=extra_services_price,
        final_price=final_price,
    )