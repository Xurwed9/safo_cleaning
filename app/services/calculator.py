from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extra_service import ExtraService
from app.models.pricing import Pricing


async def calculate_lead_price(
    db: AsyncSession,
    object_type: str,
    area: Decimal,
    extra_service_ids: list[int],
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    list[tuple[ExtraService, Decimal]],
]:
    pricing = await db.scalar(
        select(Pricing).where(
            Pricing.object_type == object_type,
            Pricing.is_active.is_(True),
        )
    )

    if not pricing:
        raise HTTPException(
            status_code=400,
            detail="Pricing for this object type is not configured",
        )

    base_price = pricing.price_per_m2 * area

    discount = Decimal("0")

    if (
        pricing.discount_threshold_m2 is not None
        and area >= pricing.discount_threshold_m2
        and pricing.discount_percent > 0
    ):
        discount = (
            base_price
            * pricing.discount_percent
            / Decimal("100")
        )

    price_after_discount = base_price - discount

    if price_after_discount < pricing.minimum_order:
        price_after_discount = pricing.minimum_order

    if not extra_service_ids:
        return (
            price_after_discount,
            base_price,
            discount,
            [],
        )

    unique_service_ids = set(extra_service_ids)

    result = await db.scalars(
        select(ExtraService).where(
            ExtraService.id.in_(unique_service_ids),
            ExtraService.is_active.is_(True),
        )
    )

    services = list(result.all())

    found_ids = {service.id for service in services}

    missing_ids = unique_service_ids - found_ids

    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Extra services not found: {sorted(missing_ids)}",
        )

    extra_services_price = Decimal("0")

    service_snapshots: list[
        tuple[ExtraService, Decimal]
    ] = []

    for service in services:

        if service.pricing_type == "fixed":
            service_total = service.price

        elif service.pricing_type == "per_m2":
            service_total = service.price * area

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported pricing type: "
                    f"{service.pricing_type}"
                ),
            )

        extra_services_price += service_total

        service_snapshots.append(
            (service, service_total)
        )

    final_price = (
        price_after_discount
        + extra_services_price
    )

    return (
        final_price,
        base_price,
        discount,
        service_snapshots,
    )