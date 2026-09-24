from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserSettings
from app.models.review import ReviewTemplate, ReviewTemplateItem

DEFAULT_SECTIONS = [
    "What I Accomplished Today",
    "Current Goals",
    "Personal Reflections",
    "Problems I Encountered",
]


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count(self) -> int:
        return await self.db.scalar(select(func.count()).select_from(User)) or 0

    async def get_by_username(self, username: str) -> User | None:
        return await self.db.scalar(select(User).where(User.username == username))

    async def get(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def create(self, username: str, password_hash: str) -> User:
        user = User(username=username, password_hash=password_hash)
        self.db.add(user)
        await self.db.flush()
        self.db.add(UserSettings(user_id=user.id))
        template = ReviewTemplate(user_id=user.id)
        self.db.add(template)
        await self.db.flush()
        self.db.add_all(
            ReviewTemplateItem(template_id=template.id, title=title, sort_order=index)
            for index, title in enumerate(DEFAULT_SECTIONS)
        )
        await self.db.flush()
        return user
