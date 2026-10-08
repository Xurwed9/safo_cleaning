import asyncio
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password


async def create_user():
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    role = input("Role (owner/manager/editor): ").strip()

    if role not in {"owner", "manager", "editor"}:
        print("Invalid role")
        return

    async with AsyncSessionLocal() as db:

        existing_user = await db.scalar(
            select(User).where(
                User.username == username
            )
        )

        if existing_user:
            print("User already exists")
            return

        now = datetime.now(timezone.utc)

        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        db.add(user)

        await db.commit()
        await db.refresh(user)

        print()
        print("User created successfully!")
        print(f"id: {user.id}")
        print(f"username: {user.username}")
        print(f"role: {user.role}")


if __name__ == "__main__":
    asyncio.run(create_user())





# import sys
# from pathlib import Path

# sys.path.append(
#     str(Path(__file__).resolve().parent.parent)
# )

# import asyncio
# from datetime import datetime, timezone

# from sqlalchemy import select

# from app.core.security import hash_password
# from app.db.session import AsyncSessionLocal
# from app.models.user import User


# async def create_owner():
#     username = "admin"
#     password = "Admin12345"

#     async with AsyncSessionLocal() as db:

#         existing_user = await db.scalar(
#             select(User).where(
#                 User.username == username
#             )
#         )

#         if existing_user:
#             print("Owner already exists")
#             return

#         now = datetime.now(timezone.utc)

#         owner = User(
#             username=username,
#             password_hash=hash_password(password),
#             role="owner",
#             is_active=True,
#             created_at=now,
#             updated_at=now,
#         )

#         db.add(owner)

#         await db.commit()

#         print("Owner created successfully")
#         print(f"Username: {username}")
#         print(f"Password: {password}")


# if __name__ == "__main__":
#     asyncio.run(create_owner())