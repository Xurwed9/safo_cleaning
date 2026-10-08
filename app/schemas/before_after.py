from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BeforeAfterTranslationCreate(BaseModel):
    language: str = Field(
        min_length=2,
        max_length=10,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )


class BeforeAfterTranslationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    language: str
    title: str
    description: str | None


class BeforeAfterResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    title: str
    description: str | None
    before_image: str
    after_image: str
    is_published: bool
    created_at: datetime
    updated_at: datetime
    translations: list[
        BeforeAfterTranslationResponse
    ]