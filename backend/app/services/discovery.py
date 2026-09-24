from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, GoalEvent, GoalTask
from app.models.review import Review, ReviewSection, ReviewSectionPreset, ReviewSnapshot
from app.models.user import UserSettings
from app.schemas.discovery import SearchResult, StatsSummary, TimelineEntry


class DiscoveryService:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id

    async def search(
        self,
        keyword: str,
        result_type: str | None,
        date_from: date | None,
        date_to: date | None,
        section_label: str | None,
        limit: int,
    ) -> tuple[list[SearchResult], int]:
        pattern = f"%{keyword.strip()}%"
        results: list[SearchResult] = []
        total = 0

        if result_type in (None, "review"):
            filters = [Review.user_id == self.user_id, Review.deleted_at.is_(None)]
            if date_from:
                filters.append(Review.review_date >= date_from)
            if date_to:
                filters.append(Review.review_date <= date_to)
            if keyword:
                matching_sections = select(ReviewSection.review_id).where(
                    ReviewSection.deleted_at.is_(None),
                    or_(ReviewSection.title.ilike(pattern), ReviewSection.content_markdown.ilike(pattern)),
                )
                filters.append(or_(Review.review_date.cast(String).ilike(pattern), Review.id.in_(matching_sections)))
            total += await self.db.scalar(select(func.count()).select_from(Review).where(*filters)) or 0
            rows = await self.db.scalars(select(Review).where(*filters).order_by(Review.review_date.desc()).limit(limit))
            results.extend(
                SearchResult(type="review", id=row.id, title=f"Daily Review · {row.review_date}", snippet=row.status, date=row.review_date)
                for row in rows
            )

        if result_type in (None, "section"):
            filters = [
                Review.user_id == self.user_id,
                Review.deleted_at.is_(None),
                ReviewSection.deleted_at.is_(None),
            ]
            if keyword:
                filters.append(or_(ReviewSection.title.ilike(pattern), ReviewSection.content_markdown.ilike(pattern)))
            if date_from:
                filters.append(Review.review_date >= date_from)
            if date_to:
                filters.append(Review.review_date <= date_to)
            if section_label:
                filters.append(ReviewSection.title.ilike(section_label))
            base = select(ReviewSection, Review.review_date).join(Review, Review.id == ReviewSection.review_id).where(*filters)
            total += await self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
            rows = (await self.db.execute(base.order_by(Review.review_date.desc()).limit(limit))).all()
            results.extend(
                SearchResult(
                    type="section",
                    id=section.id,
                    title=section.title,
                    snippet=section.content_markdown[:180],
                    date=review_date,
                    metadata={"review_id": str(section.review_id)},
                )
                for section, review_date in rows
            )

        if result_type in (None, "preset") and not date_from and not date_to:
            filters = [ReviewSectionPreset.user_id == self.user_id, ReviewSectionPreset.deleted_at.is_(None)]
            if keyword:
                filters.append(ReviewSectionPreset.title.ilike(pattern))
            if section_label:
                filters.append(ReviewSectionPreset.title.ilike(section_label))
            total += await self.db.scalar(select(func.count()).select_from(ReviewSectionPreset).where(*filters)) or 0
            rows = await self.db.scalars(select(ReviewSectionPreset).where(*filters).limit(limit))
            results.extend(SearchResult(type="preset", id=row.id, title=row.title, snippet="Section label", date=None) for row in rows)

        if result_type in (None, "goal") and not date_from and not date_to and not section_label:
            filters = [Goal.user_id == self.user_id, Goal.deleted_at.is_(None)]
            if keyword:
                filters.append(or_(Goal.title.ilike(pattern), Goal.description.ilike(pattern)))
            total += await self.db.scalar(select(func.count()).select_from(Goal).where(*filters)) or 0
            rows = await self.db.scalars(select(Goal).where(*filters).order_by(Goal.created_at.desc()).limit(limit))
            results.extend(
                SearchResult(type="goal", id=row.id, title=row.title, snippet=row.description[:180], date=row.start_date, metadata={"status": row.status})
                for row in rows
            )

        if result_type in (None, "task") and not date_from and not date_to and not section_label:
            filters = [Goal.user_id == self.user_id, Goal.deleted_at.is_(None), GoalTask.deleted_at.is_(None)]
            if keyword:
                filters.append(or_(GoalTask.title.ilike(pattern), GoalTask.description.ilike(pattern)))
            base = select(GoalTask).join(Goal, Goal.id == GoalTask.goal_id).where(*filters)
            total += await self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
            rows = await self.db.scalars(base.order_by(GoalTask.created_at.desc()).limit(limit))
            results.extend(
                SearchResult(type="task", id=row.id, title=row.title, snippet=row.description[:180], date=row.due_date, metadata={"goal_id": str(row.goal_id), "status": row.status})
                for row in rows
            )

        results.sort(key=lambda item: item.date or date.min, reverse=True)
        return results, total

    async def timeline(self, kind: str | None, limit: int) -> tuple[list[TimelineEntry], int]:
        entries: list[TimelineEntry] = []
        total = 0
        if kind in (None, "reviews"):
            review_filters = [Review.user_id == self.user_id, Review.deleted_at.is_(None)]
            total += await self.db.scalar(select(func.count()).select_from(Review).where(*review_filters)) or 0
            reviews = await self.db.scalars(select(Review).where(*review_filters).order_by(Review.created_at.desc()).limit(limit))
            entries.extend(TimelineEntry(type="review_created", id=row.id, title=f"Review created · {row.review_date}", occurred_at=row.created_at, metadata={"review_id": str(row.id)}) for row in reviews)
            snapshot_base = select(ReviewSnapshot, Review).join(Review, Review.id == ReviewSnapshot.review_id).where(*review_filters)
            total += await self.db.scalar(select(func.count()).select_from(snapshot_base.subquery())) or 0
            snapshots = (await self.db.execute(snapshot_base.order_by(ReviewSnapshot.created_at.desc()).limit(limit))).all()
            entries.extend(TimelineEntry(type="review_completed", id=snapshot.id, title=f"Review completed · {review.review_date}", occurred_at=snapshot.created_at, metadata={"review_id": str(review.id), "version": snapshot.version}) for snapshot, review in snapshots)

        if kind in (None, "goals", "tasks"):
            filters = [Goal.user_id == self.user_id]
            if kind == "tasks":
                filters.append(GoalEvent.event_type.like("task_%"))
            elif kind == "goals":
                filters.append(GoalEvent.event_type.not_like("task_%"))
            base = select(GoalEvent, Goal.title).join(Goal, Goal.id == GoalEvent.goal_id).where(*filters)
            total += await self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
            events = (await self.db.execute(base.order_by(GoalEvent.created_at.desc()).limit(limit))).all()
            entries.extend(TimelineEntry(type=event.event_type, id=event.id, title=f"{event.event_type.replace('_', ' ').title()} · {title}", occurred_at=event.created_at, metadata={**event.event_data, "goal_id": str(event.goal_id)}) for event, title in events)

        entries.sort(key=lambda entry: entry.occurred_at, reverse=True)
        return entries, total

    async def stats(self) -> StatsSummary:
        timezone = await self.db.scalar(select(UserSettings.timezone).where(UserSettings.user_id == self.user_id)) or "UTC"
        try:
            zone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            zone = ZoneInfo("UTC")
        today = datetime.now(UTC).astimezone(zone).date()
        month_start = today.replace(day=1)
        dates = list(await self.db.scalars(
            select(Review.review_date)
            .where(Review.user_id == self.user_id, Review.status == "completed", Review.deleted_at.is_(None))
            .order_by(Review.review_date.desc())
        ))
        current = 0
        if dates and dates[0] >= today - timedelta(days=1):
            expected = dates[0]
            for item in dates:
                if item != expected:
                    break
                current += 1
                expected -= timedelta(days=1)
        longest = running = 0
        previous = None
        for item in reversed(dates):
            running = running + 1 if previous and item == previous + timedelta(days=1) else 1
            longest = max(longest, running)
            previous = item
        active_goals = await self.db.scalar(select(func.count()).select_from(Goal).where(Goal.user_id == self.user_id, Goal.status == "active", Goal.deleted_at.is_(None))) or 0
        completed_goals = await self.db.scalar(select(func.count()).select_from(Goal).where(Goal.user_id == self.user_id, Goal.status == "completed", Goal.deleted_at.is_(None))) or 0
        task_total = await self.db.scalar(select(func.count()).select_from(GoalTask).join(Goal).where(Goal.user_id == self.user_id, Goal.deleted_at.is_(None), GoalTask.deleted_at.is_(None))) or 0
        task_completed = await self.db.scalar(select(func.count()).select_from(GoalTask).join(Goal).where(Goal.user_id == self.user_id, Goal.deleted_at.is_(None), GoalTask.deleted_at.is_(None), GoalTask.status == "completed")) or 0
        return StatsSummary(
            reviews_completed_this_month=sum(item >= month_start for item in dates),
            current_review_streak=current,
            longest_review_streak=longest,
            active_goals=active_goals,
            completed_goals=completed_goals,
            goal_tasks_completed=task_completed,
            goal_tasks_total=task_total,
        )
