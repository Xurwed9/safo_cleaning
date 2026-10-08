from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PricingCreate(BaseModel):
    object_type: str = Field(
        min_length=1,
        max_length=50,
    )

    price_per_m2: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    minimum_order: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    discount_threshold_m2: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    discount_percent: Decimal = Field(
        default=0,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )

    is_active: bool = True


class PricingUpdate(BaseModel):
    object_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    price_per_m2: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    minimum_order: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    discount_threshold_m2: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    discount_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )

    is_active: bool | None = None


class PricingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    object_type: str
    price_per_m2: Decimal
    minimum_order: Decimal
    discount_threshold_m2: Decimal | None
    discount_percent: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime



class PricingCalculateRequest(BaseModel):
    object_type: str = Field(
        min_length=1,
        max_length=50,
    )
    area: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    extra_service_ids: list[int] = Field(
        default_factory=list,
    )


class PricingCalculateResponse(BaseModel):
    object_type: str
    area: Decimal
    base_price: Decimal
    discount: Decimal
    extra_services_price: Decimal
    final_price: Decimal