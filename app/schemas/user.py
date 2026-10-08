from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=255)
    role: str = Field(default="manager", pattern="^(owner|manager|editor)$")


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )
    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=255,
    )
    role: str | None = Field(
        default=None,
        pattern="^(owner|manager|editor)$",
    )
    is_active: bool | None = None


class UserAdminResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True,
    }