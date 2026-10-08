from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class LeadCreate(BaseModel):
    object_type: str = Field(
        min_length=1,
        max_length=50,
    )

    area: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    cleaning_frequency: str = Field(
        min_length=1,
        max_length=50,
    )

    extra_service_ids: list[int] = Field(
        default_factory=list,
    )

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    phone: str = Field(
        min_length=5,
        max_length=30,
    )

    comment: str | None = Field(
        default=None,
        max_length=2000,
    )

    language: str = Field(
        default="ru",
        min_length=2,
        max_length=10,
    )

    consent_given: bool


class LeadResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    object_type: str
    area: Decimal
    cleaning_frequency: str
    name: str
    phone: str
    comment: str | None
    language: str
    calculated_price: Decimal
    consent_given: bool
    status: str
    assigned_manager_id: int | None
    created_at: datetime
    updated_at: datetime


class LeadStatusUpdate(BaseModel):
    status: str


class LeadAssignRequest(BaseModel):
    manager_id: int | None


class LeadNoteCreate(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=5000,
    )


class LeadNoteResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    lead_id: int
    user_id: int
    text: str
    created_at: datetime


class LeadAdminListResponse(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    page_size: int
    pages: int


class LeadManagerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class LeadExtraServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    extra_service_id: int
    price_at_submission: Decimal

    service_name: str


class LeadNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    status: str
    attempts: int
    error_message: str | None
    next_attempt_at: datetime | None
    sent_at: datetime | None
    created_at: datetime


class LeadNoteAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    user_id: int
    text: str
    created_at: datetime

    author_username: str


class LeadAdminDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    object_type: str
    area: Decimal
    cleaning_frequency: str

    name: str
    phone: str
    comment: str | None
    language: str

    calculated_price: Decimal

    consent_given: bool
    consent_at: datetime | None

    status: str

    assigned_manager_id: int | None
    assigned_manager: LeadManagerResponse | None

    extra_services: list[LeadExtraServiceResponse]
    notes: list[LeadNoteAdminResponse]
    notifications: list[LeadNotificationResponse]

    created_at: datetime
    updated_at: datetime