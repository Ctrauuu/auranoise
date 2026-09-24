from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.goal import Goal, GoalTask
from app.models.review import Review, ReviewSection, ReviewSectionPreset
from app.models.user import UserSettings
from app.schemas.data import TrashItem


class TrashService:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id

    async def cleanup(self) -> None:
        retention = await self.db.scalar(
            select(UserSettings.trash_retention_days).where(UserSettings.user_id == self.user_id)
        )
        if retention is None:
            return
        cutoff = datetime.now(UTC) - timedelta(days=retention)
        review_ids = select(Review.id).where(Review.user_id == self.user_id)
        goal_ids = select(Goal.id).where(Goal.user_id == self.user_id)
        await self.db.execute(delete(ReviewSection).where(ReviewSection.review_id.in_(review_ids), ReviewSection.deleted_at < cutoff))
        await self.db.execute(delete(GoalTask).where(GoalTask.goal_id.in_(goal_ids), GoalTask.deleted_at < cutoff))
        await self.db.execute(delete(ReviewSectionPreset).where(ReviewSectionPreset.user_id == self.user_id, ReviewSectionPreset.deleted_at < cutoff))
        await self.db.execute(delete(Review).where(Review.user_id == self.user_id, Review.deleted_at < cutoff))
        await self.db.execute(delete(Goal).where(Goal.user_id == self.user_id, Goal.deleted_at < cutoff))
        await self.db.commit()

    async def list(self) -> list[TrashItem]:
        await self.cleanup()
        items: list[TrashItem] = []
        reviews = await self.db.scalars(select(Review).where(Review.user_id == self.user_id, Review.deleted_at.is_not(None)))
        items.extend(TrashItem(type="review", id=item.id, title=f"Daily Review · {item.review_date}", deleted_at=item.deleted_at, metadata={"review_date": item.review_date.isoformat()}) for item in reviews)
        presets = await self.db.scalars(select(ReviewSectionPreset).where(ReviewSectionPreset.user_id == self.user_id, ReviewSectionPreset.deleted_at.is_not(None)))
        items.extend(TrashItem(type="preset", id=item.id, title=item.title, deleted_at=item.deleted_at) for item in presets)
        goals = await self.db.scalars(select(Goal).where(Goal.user_id == self.user_id, Goal.deleted_at.is_not(None)))
        items.extend(TrashItem(type="goal", id=item.id, title=item.title, deleted_at=item.deleted_at) for item in goals)
        sections = await self.db.execute(select(ReviewSection).join(Review).where(Review.user_id == self.user_id, ReviewSection.deleted_at.is_not(None)))
        items.extend(TrashItem(type="section", id=item.id, title=item.title, deleted_at=item.deleted_at, metadata={"review_id": str(item.review_id)}) for item in sections.scalars())
        tasks = await self.db.execute(select(GoalTask).join(Goal).where(Goal.user_id == self.user_id, GoalTask.deleted_at.is_not(None)))
        items.extend(TrashItem(type="task", id=item.id, title=item.title, deleted_at=item.deleted_at, metadata={"goal_id": str(item.goal_id)}) for item in tasks.scalars())
        items.sort(key=lambda item: item.deleted_at, reverse=True)
        return items

    async def resource(self, kind: str, resource_id: UUID):
        if kind == "review":
            resource = await self.db.scalar(select(Review).where(Review.id == resource_id, Review.user_id == self.user_id))
        elif kind == "preset":
            resource = await self.db.scalar(select(ReviewSectionPreset).where(ReviewSectionPreset.id == resource_id, ReviewSectionPreset.user_id == self.user_id))
        elif kind == "goal":
            resource = await self.db.scalar(select(Goal).where(Goal.id == resource_id, Goal.user_id == self.user_id))
        elif kind == "section":
            resource = await self.db.scalar(select(ReviewSection).join(Review).where(ReviewSection.id == resource_id, Review.user_id == self.user_id))
        elif kind == "task":
            resource = await self.db.scalar(select(GoalTask).join(Goal).where(GoalTask.id == resource_id, Goal.user_id == self.user_id))
        else:
            raise AppError(404, "TRASH_TYPE_NOT_FOUND", "Unknown trash item type")
        if not resource or resource.deleted_at is None:
            raise AppError(404, "TRASH_ITEM_NOT_FOUND", "Trash item not found")
        return resource

    async def restore(self, kind: str, resource_id: UUID) -> None:
        resource = await self.resource(kind, resource_id)
        resource.deleted_at = None
        await self.db.commit()

    async def permanently_delete(self, kind: str, resource_id: UUID) -> None:
        resource = await self.resource(kind, resource_id)
        await self.db.delete(resource)
        await self.db.commit()

