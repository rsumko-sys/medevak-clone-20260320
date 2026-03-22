"""
seed_users.py — створює тестових користувачів у локальній базі даних.

Використання:
    cd backend
    python seed_users.py

Буде створено (або пропущено якщо вже існує):
    admin@azov.ua   / Admin2026!   — роль: admin
    medic@azov.ua   / Medic2026!   — роль: medic
"""

import asyncio
import sys
import os
import uuid

# Щоб Python знайшов app.*
sys.path.insert(0, os.path.dirname(__file__))

import bcrypt
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.user import User

SEED_USERS = [
    {
        "email": "admin@azov.ua",
        "password": "Admin2026!",
        "role": "admin",
        "unit": "HQ",
    },
    {
        "email": "medic@azov.ua",
        "password": "Medic2026!",
        "role": "medic",
        "unit": "Alpha",
    },
]


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode(), salt).decode()


async def seed() -> None:
    # Переконуємось що таблиці існують
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        skipped = 0

        for user_data in SEED_USERS:
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  SKIP  {user_data['email']}  (вже існує, роль={existing.role})")
                skipped += 1
                continue

            user = User(
                id=str(uuid.uuid4()),
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                unit=user_data.get("unit"),
                is_active=True,
            )
            session.add(user)
            created += 1
            print(f"  CREATE {user_data['email']}  роль={user_data['role']}  пароль={user_data['password']}")

        await session.commit()

    print()
    print(f"  Готово: створено {created}, пропущено {skipped}")
    print()
    print("  Для входу:")
    for u in SEED_USERS:
        print(f"    {u['email']}  /  {u['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
