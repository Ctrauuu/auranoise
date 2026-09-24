from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.goal import Goal, GoalEvent, GoalTask, ReviewGoal
from app.models.review import Review
from app.repositories.goal import GoalRepository
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate, TaskCreate, TaskResponse, TaskUpdate


class GoalService:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self.goals = GoalRepository(db)

    async def get(self, goal_id: UUID) -> Goal:
        goal = await self.goals.get(goal_id, self.user_id)
        if not goal:
            raise AppError(404, "GOAL_NOT_FOUND", "Goal not found")
        return goal

    async def response(self, goal: Goal) -> GoalResponse:
        tasks = await self.goals.tasks(goal.id)
        return GoalResponse(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            status=goal.status,
            start_date=goal.start_date,
            target_date=goal.target_date,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
            tasks=[TaskResponse.model_validate(task) for task in tasks],
        )

    def event(self, goal_id: UUID, event_type: str, **data) -> None:
        self.db.add(GoalEvent(goal_id=goal_id, event_type=event_type, event_data=data))

    async def create(self, payload: GoalCreate) -> GoalResponse:
        goal = Goal(user_id=self.user_id, **payload.model_dump())
        self.db.add(goal)
        await self.db.flush()
        self.event(goal.id, "goal_created", title=goal.title)
        await self.db.commit()
        return await self.response(goal)

    async def update(self, goal_id: UUID, payload: GoalUpdate) -> GoalResponse:
        goal = await self.get(goal_id)
        old_status = goal.status
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(goal, key, value)
        if payload.status and payload.status != old_status:
            event_type = {
                "completed": "goal_completed",
                "paused": "goal_paused",
                "active": "goal_resumed" if old_status == "paused" else "goal_status_changed",
            }.get(payload.status, "goal_status_changed")
            self.event(goal.id, event_type, from_status=old_status, to_status=payload.status)
        await self.db.commit()
        await self.db.refresh(goal)
        return await self.response(goal)

    async def create_task(self, goal_id: UUID, payload: TaskCreate) -> TaskResponse:
        goal = await self.get(goal_id)
        task = GoalTask(goal_id=goal.id, **payload.model_dump())
        self.db.add(task)
        await self.db.flush()
        self.event(goal.id, "task_created", task_id=str(task.id), title=task.title)
        if task.status == "completed":
            self.event(goal.id, "task_completed", task_id=str(task.id), title=task.title)
        await self.db.commit()
        return TaskResponse.model_validate(task)

    async def task(self, task_id: UUID) -> tuple[Goal, GoalTask]:
        row = await self.db.execute(
            select(Goal, GoalTask)
            .join(GoalTask, GoalTask.goal_id == Goal.id)
            .where(
                GoalTask.id == task_id,
                Goal.user_id == self.user_id,
                Goal.deleted_at.is_(None),
                GoalTask.deleted_at.is_(None),
            )
        )
        result = row.first()
        if not result:
            raise AppError(404, "TASK_NOT_FOUND", "Goal task not found")
        return result

    async def update_task(self, task_id: UUID, payload: TaskUpdate) -> TaskResponse:
        goal, task = await self.task(task_id)
        old_status = task.status
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(task, key, value)
        if payload.status and payload.status != old_status:
            self.event(goal.id, "task_status_changed", task_id=str(task.id), from_status=old_status, to_status=payload.status)
            if payload.status == "completed":
                self.event(goal.id, "task_completed", task_id=str(task.id), title=task.title)
        await self.db.commit()
        return TaskResponse.model_validate(task)

    async def replace_review_links(self, review_id: UUID, goal_ids: list[UUID]) -> None:
        review = await self.db.scalar(
            select(Review).where(Review.id == review_id, Review.user_id == self.user_id, Review.deleted_at.is_(None))
        )
        if not review:
            raise AppError(404, "REVIEW_NOT_FOUND", "Review not found")
        unique_ids = set(goal_ids)
        if unique_ids:
            valid = set(await self.db.scalars(
                select(Goal.id).where(Goal.id.in_(unique_ids), Goal.user_id == self.user_id, Goal.deleted_at.is_(None))
            ))
            if valid != unique_ids:
                raise AppError(404, "GOAL_NOT_FOUND", "One or more goals were not found")
        existing = set(await self.db.scalars(select(ReviewGoal.goal_id).where(ReviewGoal.review_id == review_id)))
        await self.db.execute(
            delete(ReviewGoal).where(ReviewGoal.review_id == review_id, ReviewGoal.goal_id.not_in(unique_ids))
        )
        for goal_id in unique_ids - existing:
            self.db.add(ReviewGoal(review_id=review_id, goal_id=goal_id))
            self.event(goal_id, "review_linked", review_id=str(review_id), review_date=review.review_date.isoformat())
        await self.db.commit()

