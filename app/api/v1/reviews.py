from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_roles
from app.db.session import get_db
from app.models.review import Review
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
    ReviewAdminCreate,
)

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)



@router.get(
    "",
    response_model=list[ReviewResponse],
)
async def get_public_reviews(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Review)
        .where(
            Review.is_published.is_(True)
        )
        .order_by(
            Review.created_at.desc()
        )
    )

    return list(result.all())



@router.get(
    "/admin",
    response_model=list[ReviewResponse],
    dependencies=[
        Depends(
            require_roles("owner", "editor")
        )
    ],
)
async def get_admin_reviews(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Review)
        .order_by(
            Review.created_at.desc()
        )
    )

    return list(result.all())



@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_public_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    if not data.client_consent:
        raise HTTPException(
            status_code=400,
            detail="Client consent is required",
        )

    now = datetime.now(timezone.utc)

    review = Review(
        client_name=data.client_name,
        text=data.text,
        rating=data.rating,
        language=data.language,
        client_consent=data.client_consent,
        is_published=False,
        created_at=now,
        updated_at=now,
    )

    db.add(review)

    await db.commit()
    await db.refresh(review)

    return review



@router.post(
    "/admin",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles("owner", "editor")
        )
    ],
)
async def create_review(
    data: ReviewAdminCreate,
    db: AsyncSession = Depends(get_db),
):
    if data.is_published and not data.client_consent:
        raise HTTPException(
            status_code=400,
            detail="Review cannot be published without client consent",
        )

    now = datetime.now(timezone.utc)

    review = Review(
        client_name=data.client_name,
        text=data.text,
        rating=data.rating,
        language=data.language,
        client_consent=data.client_consent,
        is_published=data.is_published,
        created_at=now,
        updated_at=now,
    )

    db.add(review)

    await db.commit()
    await db.refresh(review)

    return review



@router.patch(
    "/admin/{review_id}",
    response_model=ReviewResponse,
    dependencies=[
        Depends(
            require_roles("owner", "editor")
        )
    ],
)
async def update_review(
    review_id: int,
    data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
):
    review = await db.scalar(
        select(Review).where(
            Review.id == review_id
        )
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found",
        )

    if data.is_published and not data.client_consent:
        raise HTTPException(
            status_code=400,
            detail="Review cannot be published without client consent",
        )

    review.client_name = data.client_name
    review.text = data.text
    review.rating = data.rating
    review.language = data.language
    review.client_consent = data.client_consent
    review.is_published = data.is_published
    review.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(review)

    return review