from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    client_name: str = Field(
        min_length=2,
        max_length=150,
    )

    text: str = Field(
        min_length=1,
        max_length=5000,
    )

    rating: int = Field(
        ge=1,
        le=5,
    )

    language: str = Field(
        min_length=2,
        max_length=10,
    )

    client_consent: bool


class ReviewAdminCreate(ReviewCreate):
    is_published: bool = False


class ReviewUpdate(BaseModel):
    client_name: str = Field(
        min_length=2,
        max_length=150,
    )

    text: str = Field(
        min_length=1,
        max_length=5000,
    )

    rating: int = Field(
        ge=1,
        le=5,
    )

    language: str = Field(
        min_length=2,
        max_length=10,
    )

    client_consent: bool

    is_published: bool


class ReviewResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    client_name: str
    text: str
    rating: int
    language: str
    client_consent: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime