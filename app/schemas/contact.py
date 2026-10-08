from pydantic import BaseModel, Field, ConfigDict


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


class ContactTranslationCreate(BaseModel):
    language: str = Field(min_length=2, max_length=10)
    address: str = Field(min_length=1, max_length=2000)
    working_hours: str = Field(min_length=1, max_length=255)


class ContactTranslationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language: str
    address: str
    working_hours: str


class ContactCreate(BaseModel):
    phone: str = Field(min_length=5, max_length=30)
    whatsapp: str | None = Field(default=None, max_length=255)
    telegram: str | None = Field(default=None, max_length=255)
    instagram: str | None = Field(default=None, max_length=255)
    map_url: str | None = Field(default=None, max_length=500)

    translations: list[ContactTranslationCreate] = Field(
        default_factory=list
    )


class ContactUpdate(BaseModel):
    phone: str = Field(min_length=5, max_length=30)
    whatsapp: str | None = Field(default=None, max_length=255)
    telegram: str | None = Field(default=None, max_length=255)
    instagram: str | None = Field(default=None, max_length=255)
    map_url: str | None = Field(default=None, max_length=500)


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    whatsapp: str | None
    telegram: str | None
    instagram: str | None
    map_url: str | None

    translations: list[ContactTranslationResponse]