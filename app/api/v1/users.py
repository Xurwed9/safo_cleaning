from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserAdminResponse,
    UserCreate,
    UserUpdate,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserAdminResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("owner"))],
)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    existing_user = await db.scalar(
        select(User).where(
            User.username == data.username
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    if data.role not in {"owner", "manager", "editor"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )

    now = datetime.now(timezone.utc)

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    await db.refresh(user)

    return user


@router.get(
    "",
    response_model=list[UserAdminResponse],
    dependencies=[Depends(require_roles("owner"))],
)
async def list_users(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(User).order_by(
            User.id.asc()
        )
    )

    return list(result.all())


@router.get(
    "/{user_id}",
    response_model=UserAdminResponse,
    dependencies=[Depends(require_roles("owner"))],
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserAdminResponse,
    dependencies=[Depends(require_roles("owner"))],
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "username" in update_data:
        existing_user = await db.scalar(
            select(User).where(
                User.username == update_data["username"],
                User.id != user_id,
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

        user.username = update_data["username"]

    if "password" in update_data:
        user.password_hash = hash_password(
            update_data["password"]
        )

    if "role" in update_data:
        user.role = update_data["role"]

    if "is_active" in update_data:
        if user.id == 1 and update_data["is_active"] is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the main owner",
            )

        if (
            user.role == "owner"
            and update_data["is_active"] is False
        ):
            owner_count = await db.scalar(
                select(User.id)
                .where(
                    User.role == "owner",
                    User.is_active.is_(True),
                    User.id != user_id,
                )
                .limit(1)
            )

            if owner_count is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the last active owner",
                )

        user.is_active = update_data["is_active"]

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    await db.refresh(user)

    return user


@router.delete(
    "/{user_id}",
    response_model=UserAdminResponse,
    dependencies=[Depends(require_roles("owner"))],
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate the main owner",
        )

    if user.role == "owner":
        owner_count = await db.scalar(
            select(User.id)
            .where(
                User.role == "owner",
                User.is_active.is_(True),
                User.id != user_id,
            )
            .limit(1)
        )

        if owner_count is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active owner",
            )

    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    return user