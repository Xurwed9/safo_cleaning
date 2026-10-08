import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import require_roles
from app.db.session import get_db
from app.models.before_after import BeforeAfter
from app.models.before_after_translation import (
    BeforeAfterTranslation,
)
from app.schemas.before_after import (
    BeforeAfterResponse,
    BeforeAfterTranslationCreate,
    BeforeAfterTranslationResponse,
)

router = APIRouter(
    prefix="/before-after",
    tags=["Before / After"],
)


STORAGE_DIR = Path("storage/before_after")
STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


async def save_image(
    file: UploadFile,
) -> str:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WEBP images are allowed",
        )

    extension = Path(
        file.filename or ""
    ).suffix.lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid image extension",
        )

    filename = (
        f"{uuid4().hex}"
        f"{extension}"
    )

    destination = STORAGE_DIR / filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )

    return (
        f"/storage/before_after/{filename}"
    )



@router.get(
    "",
    response_model=list[BeforeAfterResponse],
)
async def get_public_before_after(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(BeforeAfter)
        .options(
            selectinload(
                BeforeAfter.translations
            )
        )
        .where(
            BeforeAfter.is_published.is_(True)
        )
        .order_by(
            BeforeAfter.created_at.desc()
        )
    )

    return list(result.all())



@router.get(
    "/admin",
    response_model=list[BeforeAfterResponse],
    dependencies=[
        Depends(
            require_roles(
                "owner",
                "editor",
            )
        )
    ],
)
async def get_admin_before_after(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(BeforeAfter)
        .options(
            selectinload(
                BeforeAfter.translations
            )
        )
        .order_by(
            BeforeAfter.created_at.desc()
        )
    )

    return list(result.all())



@router.post(
    "/admin",
    response_model=BeforeAfterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(
                "owner",
                "editor",
            )
        )
    ],
)
async def create_before_after(
    title: str = Form(...),
    description: str | None = Form(None),
    is_published: bool = Form(False),
    before_image: UploadFile = File(...),
    after_image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    before_path = await save_image(
        before_image
    )

    try:
        after_path = await save_image(
            after_image
        )
    except Exception:
        before_file = Path(
            before_path.lstrip("/")
        )

        if before_file.exists():
            before_file.unlink()

        raise

    now = datetime.now(timezone.utc)

    item = BeforeAfter(
        title=title,
        description=description,
        before_image=before_path,
        after_image=after_path,
        is_published=is_published,
        created_at=now,
        updated_at=now,
    )

    db.add(item)

    await db.commit()

    await db.refresh(item)

    return item



@router.patch(
    "/admin/{before_after_id}",
    response_model=BeforeAfterResponse,
    dependencies=[
        Depends(
            require_roles(
                "owner",
                "editor",
            )
        )
    ],
)
async def update_before_after(
    before_after_id: int,
    title: str = Form(...),
    description: str | None = Form(None),
    is_published: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(BeforeAfter)
        .options(
            selectinload(
                BeforeAfter.translations
            )
        )
        .where(
            BeforeAfter.id
            == before_after_id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Before / After not found",
        )

    item.title = title
    item.description = description
    item.is_published = is_published
    item.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(item)

    return item



@router.patch(
    "/admin/{before_after_id}/images",
    response_model=BeforeAfterResponse,
    dependencies=[
        Depends(
            require_roles(
                "owner",
                "editor",
            )
        )
    ],
)
async def update_before_after_images(
    before_after_id: int,
    before_image: UploadFile | None = File(None),
    after_image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(BeforeAfter)
        .options(
            selectinload(
                BeforeAfter.translations
            )
        )
        .where(
            BeforeAfter.id
            == before_after_id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Before / After not found",
        )

    old_before = item.before_image
    old_after = item.after_image

    if before_image:
        item.before_image = (
            await save_image(before_image)
        )

    if after_image:
        item.after_image = (
            await save_image(after_image)
        )

    item.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(item)

    for old_path, new_path in [
        (old_before, item.before_image),
        (old_after, item.after_image),
    ]:
        if old_path != new_path:
            old_file = Path(
                old_path.lstrip("/")
            )

            if old_file.exists():
                old_file.unlink()

    return item



@router.post(
    "/admin/{before_after_id}/translations",
    response_model=BeforeAfterResponse,
    dependencies=[
        Depends(
            require_roles(
                "owner",
                "editor",
            )
        )
    ],
)
async def add_before_after_translation(
    before_after_id: int,
    data: BeforeAfterTranslationCreate,
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(BeforeAfter)
        .options(
            selectinload(
                BeforeAfter.translations
            )
        )
        .where(
            BeforeAfter.id
            == before_after_id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Before / After not found",
        )

    existing = await db.scalar(
        select(BeforeAfterTranslation).where(
            BeforeAfterTranslation.before_after_id
            == before_after_id,
            BeforeAfterTranslation.language
            == data.language,
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=(
                "Translation for this "
                "language already exists"
            ),
        )

    translation = BeforeAfterTranslation(
        before_after_id=before_after_id,
        language=data.language,
        title=data.title,
        description=data.description,
    )

    db.add(translation)

    await db.commit()

    await db.refresh(item)

    return item



@router.patch(
    "/admin/translations/{translation_id}",
    response_model=BeforeAfterTranslationResponse,
    dependencies=[
        Depends(
            require_roles(
                "owner",
                "editor",
            )
        )
    ],
)
async def update_before_after_translation(
    translation_id: int,
    data: BeforeAfterTranslationCreate,
    db: AsyncSession = Depends(get_db),
):
    translation = await db.scalar(
        select(
            BeforeAfterTranslation
        ).where(
            BeforeAfterTranslation.id
            == translation_id
        )
    )

    if not translation:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )

    if (
        translation.language
        != data.language
    ):
        existing = await db.scalar(
            select(
                BeforeAfterTranslation
            ).where(
                BeforeAfterTranslation.before_after_id
                == translation.before_after_id,
                BeforeAfterTranslation.language
                == data.language,
                BeforeAfterTranslation.id
                != translation_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Translation for this "
                    "language already exists"
                ),
            )

    translation.language = data.language
    translation.title = data.title
    translation.description = data.description

    await db.commit()
    await db.refresh(translation)

    return translation