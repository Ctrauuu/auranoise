from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository


async def bootstrap_initial_user(db: AsyncSession) -> User | None:
    repository = UserRepository(db)
    if await repository.count():
        return None
    user = await repository.create(settings.initial_username, hash_password(settings.initial_password))
    await db.commit()
    return user


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    async def login(self, username: str, password: str) -> str:
        user = await self.users.get_by_username(username)
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise AppError(401, "INVALID_CREDENTIALS", "Invalid username or password")
        return create_access_token(user.id, user.username)

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise AppError(400, "INVALID_PASSWORD", "Current password is incorrect")
        user.password_hash = hash_password(new_password)
        await self.db.commit()

