from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import require_roles
from app.db.session import get_db
from app.models.contact import Contact
from app.models.contact_translation import ContactTranslation
from app.models.user import User
from app.schemas.contact import (
    ContactCreate,
    ContactResponse,
    ContactTranslationCreate,
    ContactUpdate,
    SUPPORTED_LANGUAGES,
    ContactTranslationResponse,
)

router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
)


@router.get(
    "",
    response_model=list[ContactResponse],
)
async def get_contacts(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Contact)
        .options(
            selectinload(Contact.translations)
        )
        .order_by(Contact.id)
    )

    return list(result.all())



@router.post(
    "/admin",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contact(
    data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "editor")
    ),
):
    languages = [
        translation.language
        for translation in data.translations
    ]

    if len(languages) != len(set(languages)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate translation language",
        )

    invalid_languages = (
        set(languages) - SUPPORTED_LANGUAGES
    )

    if invalid_languages:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported languages: "
                f"{sorted(invalid_languages)}"
            ),
        )

    now = datetime.now(timezone.utc)

    contact = Contact(
        phone=data.phone,
        whatsapp=data.whatsapp,
        telegram=data.telegram,
        instagram=data.instagram,
        map_url=data.map_url,
        created_at=now,
        updated_at=now,
    )

    db.add(contact)

    await db.flush()

    for translation_data in data.translations:
        translation = ContactTranslation(
            contact_id=contact.id,
            language=translation_data.language,
            address=translation_data.address,
            working_hours=translation_data.working_hours,
        )

        db.add(translation)

    await db.commit()

    result = await db.scalar(
        select(Contact)
        .options(
            selectinload(Contact.translations)
        )
        .where(Contact.id == contact.id)
    )

    return result




@router.patch(
    "/admin/{contact_id}",
    response_model=ContactResponse,
)
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("owner", "editor")
    ),
):
    contact = await db.scalar(
        select(Contact).where(
            Contact.id == contact_id
        )
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    if "phone" in data.model_fields_set:
        contact.phone = data.phone

    if "whatsapp" in data.model_fields_set:
        contact.whatsapp = data.whatsapp

    if "telegram" in data.model_fields_set:
        contact.telegram = data.telegram

    if "instagram" in data.model_fields_set:
        contact.instagram = data.instagram

    if "map_url" in data.model_fields_set:
        contact.map_url = data.map_url
    contact.updated_at = datetime.now(timezone.utc)

    await db.commit()

    result = await db.scalar(
    select(Contact)
        .options(
            selectinload(Contact.translations)
        )
        .where(Contact.id == contact.id)
    )

    return result



@router.post(
    "/admin/{contact_id}/translations",
    response_model=ContactTranslationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contact_translation(
    contact_id: int,
    data: ContactTranslationCreate,
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

    contact = await db.scalar(
        select(Contact).where(
            Contact.id == contact_id
        )
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    existing = await db.scalar(
        select(ContactTranslation).where(
            ContactTranslation.contact_id == contact_id,
            ContactTranslation.language == data.language,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Translation already exists",
        )

    translation = ContactTranslation(
        contact_id=contact_id,
        language=data.language,
        address=data.address,
        working_hours=data.working_hours,
    )

    db.add(translation)

    await db.commit()
    await db.refresh(translation)

    return translation



@router.patch(
    "/admin/translations/{translation_id}",
    response_model=ContactTranslationResponse,
)
async def update_contact_translation(
    translation_id: int,
    data: ContactTranslationCreate,
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
        select(ContactTranslation).where(
            ContactTranslation.id == translation_id
        )
    )

    if not translation:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )

    duplicate = await db.scalar(
        select(ContactTranslation).where(
            ContactTranslation.contact_id
            == translation.contact_id,
            ContactTranslation.language
            == data.language,
            ContactTranslation.id
            != translation.id,
        )
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Translation already exists",
        )

    translation.language = data.language
    translation.address = data.address
    translation.working_hours = data.working_hours

    await db.commit()
    await db.refresh(translation)

    return translation