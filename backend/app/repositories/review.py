from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import (
    Review,
    ReviewSection,
    ReviewSectionPreset,
    ReviewTemplate,
    ReviewTemplateItem,
)


class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, review_id: UUID, user_id: UUID, include_deleted: bool = False) -> Review | None:
        query = select(Review).where(Review.id == review_id, Review.user_id == user_id)
        if not include_deleted:
            query = query.where(Review.deleted_at.is_(None))
        return await self.db.scalar(query)

    async def get_by_date(self, user_id: UUID, review_date: date) -> Review | None:
        return await self.db.scalar(
            select(Review).where(
                Review.user_id == user_id,
                Review.review_date == review_date,
                Review.deleted_at.is_(None),
            )
        )

    async def sections(self, review_id: UUID) -> list[ReviewSection]:
        result = await self.db.scalars(
            select(ReviewSection)
            .where(ReviewSection.review_id == review_id, ReviewSection.deleted_at.is_(None))
            .order_by(ReviewSection.sort_order)
        )
        return list(result)

    async def list(
        self, user_id: UUID, page: int, page_size: int, date_from: date | None, date_to: date | None
    ) -> tuple[list[Review], int]:
        filters = [Review.user_id == user_id, Review.deleted_at.is_(None)]
        if date_from:
            filters.append(Review.review_date >= date_from)
        if date_to:
            filters.append(Review.review_date <= date_to)
        total = await self.db.scalar(select(func.count()).select_from(Review).where(*filters)) or 0
        rows = await self.db.scalars(
            select(Review)
            .where(*filters)
            .order_by(Review.review_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows), total

    async def template(self, user_id: UUID) -> tuple[ReviewTemplate, list[ReviewTemplateItem]]:
        template = await self.db.scalar(select(ReviewTemplate).where(ReviewTemplate.user_id == user_id))
        if not template:
            raise RuntimeError("User template is missing")
        items = await self.db.scalars(
            select(ReviewTemplateItem)
            .where(ReviewTemplateItem.template_id == template.id)
            .order_by(ReviewTemplateItem.sort_order)
        )
        return template, list(items)

    async def replace_template(self, template_id: UUID, items: list[tuple[str, int]]) -> None:
        await self.db.execute(delete(ReviewTemplateItem).where(ReviewTemplateItem.template_id == template_id))
        self.db.add_all(
            ReviewTemplateItem(template_id=template_id, title=title, sort_order=order)
            for title, order in items
        )
