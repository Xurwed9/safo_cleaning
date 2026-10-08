from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


SUPPORTED_LANGUAGES = {
    "ru",
    "tj",
    "en",
    "uz",
    "kk",
    "ky",
    "az",
    "tr",
    "ar",
    "de",
    "zh",
}


class ExtraServiceTranslationCreate(BaseModel):
    language: str = Field(
        min_length=2,
        max_length=10,
    )

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )


class ExtraServiceTranslationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    language: str
    name: str
    description: str | None


class ExtraServiceCreate(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=50,
    )

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    price: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    pricing_type: str = Field(
        default="fixed",
        pattern="^(fixed|per_m2)$",
    )

    is_active: bool = True


class ExtraServiceUpdate(BaseModel):
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    pricing_type: str | None = Field(
        default=None,
        pattern="^(fixed|per_m2)$",
    )

    is_active: bool | None = None


class ExtraServiceResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    code: str
    name: str
    price: Decimal
    pricing_type: str
    is_active: bool

    translations: list[
        ExtraServiceTranslationResponse
    ]