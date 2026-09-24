from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, GoalTask


class GoalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, goal_id: UUID, user_id: UUID, include_deleted: bool = False) -> Goal | None:
        query = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
        if not include_deleted:
            query = query.where(Goal.deleted_at.is_(None))
        return await self.db.scalar(query)

    async def tasks(self, goal_id: UUID) -> list[GoalTask]:
        rows = await self.db.scalars(
            select(GoalTask)
            .where(GoalTask.goal_id == goal_id, GoalTask.deleted_at.is_(None))
            .order_by(GoalTask.created_at)
        )
        return list(rows)

    async def list(self, user_id: UUID, page: int, page_size: int, status: str | None) -> tuple[list[Goal], int]:
        filters = [Goal.user_id == user_id, Goal.deleted_at.is_(None)]
        if status:
            filters.append(Goal.status == status)
        total = await self.db.scalar(select(func.count()).select_from(Goal).where(*filters)) or 0
        rows = await self.db.scalars(
            select(Goal).where(*filters).order_by(Goal.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return list(rows), total

