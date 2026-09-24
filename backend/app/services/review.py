from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.review import Review, ReviewSection, ReviewSectionPreset, ReviewSnapshot, ReviewTemplateItem
from app.models.goal import Goal, ReviewGoal
from app.models.user import UserSettings
from app.repositories.review import ReviewRepository
from app.schemas.review import ReviewResponse, SectionCreate, SectionResponse, TemplateItem


class ReviewService:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self.reviews = ReviewRepository(db)

    async def today(self) -> date:
        timezone = await self.db.scalar(select(UserSettings.timezone).where(UserSettings.user_id == self.user_id))
        try:
            zone = ZoneInfo(timezone or "UTC")
        except ZoneInfoNotFoundError:
            zone = ZoneInfo("UTC")
        return datetime.now(UTC).astimezone(zone).date()

    async def response(self, review: Review) -> ReviewResponse:
        sections = await self.reviews.sections(review.id)
        return ReviewResponse(
            id=review.id,
            review_date=review.review_date,
            status=review.status,
            created_at=review.created_at,
            updated_at=review.updated_at,
            sections=[SectionResponse.model_validate(section) for section in sections],
        )

    async def get(self, review_id: UUID) -> Review:
        review = await self.reviews.get(review_id, self.user_id)
        if not review:
            raise AppError(404, "REVIEW_NOT_FOUND", "Review not found")
        return review

    async def create(self, review_date: date) -> ReviewResponse:
        if review_date > await self.today():
            raise AppError(422, "FUTURE_REVIEW", "Reviews cannot be created for future dates")
        review = Review(user_id=self.user_id, review_date=review_date)
        self.db.add(review)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise AppError(409, "REVIEW_EXISTS", "A review already exists for this date") from None
        _, items = await self.reviews.template(self.user_id)
        self.db.add_all(
            ReviewSection(review_id=review.id, title=item.title, sort_order=item.sort_order)
            for item in items
        )
        await self.db.commit()
        return await self.response(review)

    async def add_section(self, review_id: UUID, payload: SectionCreate) -> SectionResponse:
        await self.get(review_id)
        preset_id = payload.preset_id
        if preset_id:
            preset = await self.db.scalar(
                select(ReviewSectionPreset).where(
                    ReviewSectionPreset.id == preset_id,
                    ReviewSectionPreset.user_id == self.user_id,
                    ReviewSectionPreset.deleted_at.is_(None),
                )
            )
            if not preset:
                raise AppError(404, "PRESET_NOT_FOUND", "Section preset not found")
        elif payload.save_to_library:
            preset = ReviewSectionPreset(user_id=self.user_id, title=payload.title)
            self.db.add(preset)
            await self.db.flush()
            preset_id = preset.id
        count = len(await self.reviews.sections(review_id))
        section = ReviewSection(
            review_id=review_id,
            preset_id=preset_id,
            title=payload.title,
            content_markdown=payload.content_markdown,
            sort_order=count,
        )
        self.db.add(section)
        await self.db.commit()
        return SectionResponse.model_validate(section)

    async def complete(self, review_id: UUID) -> ReviewResponse:
        review = await self.get(review_id)
        sections = await self.reviews.sections(review.id)
        linked_goals = list((await self.db.execute(
            select(Goal.id, Goal.title, Goal.status)
            .join(ReviewGoal, ReviewGoal.goal_id == Goal.id)
            .where(ReviewGoal.review_id == review.id, Goal.deleted_at.is_(None))
        )).mappings())
        version = (await self.db.scalar(
            select(func.max(ReviewSnapshot.version)).where(ReviewSnapshot.review_id == review.id)
        ) or 0) + 1
        review.status = "completed"
        self.db.add(ReviewSnapshot(
            review_id=review.id,
            version=version,
            snapshot={
                "review_id": str(review.id),
                "review_date": review.review_date.isoformat(),
                "status": "completed",
                "sections": [
                    {
                        "id": str(section.id),
                        "preset_id": str(section.preset_id) if section.preset_id else None,
                        "title": section.title,
                        "content_markdown": section.content_markdown,
                        "sort_order": section.sort_order,
                    }
                    for section in sections
                ],
                "linked_goals": [
                    {"id": str(goal["id"]), "title": goal["title"], "status": goal["status"]}
                    for goal in linked_goals
                ],
            },
        ))
        await self.db.commit()
        await self.db.refresh(review)
        return await self.response(review)

    async def owned_section(self, section_id: UUID) -> ReviewSection:
        section = await self.db.scalar(
            select(ReviewSection)
            .join(Review, Review.id == ReviewSection.review_id)
            .where(
                ReviewSection.id == section_id,
                Review.user_id == self.user_id,
                Review.deleted_at.is_(None),
                ReviewSection.deleted_at.is_(None),
            )
        )
        if not section:
            raise AppError(404, "SECTION_NOT_FOUND", "Review section not found")
        return section

    async def template(self) -> tuple[UUID, list[TemplateItem]]:
        template, items = await self.reviews.template(self.user_id)
        return template.id, [TemplateItem.model_validate(item, from_attributes=True) for item in items]
