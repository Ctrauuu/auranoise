from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.goal import GoalEvent, GoalTask, ReviewGoal
from app.schemas.goal import (
    EventResponse,
    GoalCreate,
    GoalLinks,
    GoalList,
    GoalResponse,
    GoalUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.goal import GoalService
from app.services.review import ReviewService

router = APIRouter(tags=["goals"])


@router.get("/goals", response_model=GoalList)
async def list_goals(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
):
    service = GoalService(db, user.id)
    goals, total = await service.goals.list(user.id, page, page_size, status)
    return GoalList(items=[await service.response(goal) for goal in goals], page=page, page_size=page_size, total=total)


@router.post("/goals", response_model=GoalResponse, status_code=201)
async def create_goal(payload: GoalCreate, db: DbSession, user: CurrentUser):
    return await GoalService(db, user.id).create(payload)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: UUID, db: DbSession, user: CurrentUser):
    service = GoalService(db, user.id)
    return await service.response(await service.get(goal_id))


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: UUID, payload: GoalUpdate, db: DbSession, user: CurrentUser):
    return await GoalService(db, user.id).update(goal_id, payload)


@router.delete("/goals/{goal_id}", status_code=204)
async def delete_goal(goal_id: UUID, db: DbSession, user: CurrentUser):
    goal = await GoalService(db, user.id).get(goal_id)
    goal.deleted_at = datetime.now(UTC)
    await db.commit()


@router.post("/goals/{goal_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(goal_id: UUID, payload: TaskCreate, db: DbSession, user: CurrentUser):
    return await GoalService(db, user.id).create_task(goal_id, payload)


@router.patch("/goal-tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: UUID, payload: TaskUpdate, db: DbSession, user: CurrentUser):
    return await GoalService(db, user.id).update_task(task_id, payload)


@router.delete("/goal-tasks/{task_id}", status_code=204)
async def delete_task(task_id: UUID, db: DbSession, user: CurrentUser):
    _, task = await GoalService(db, user.id).task(task_id)
    task.deleted_at = datetime.now(UTC)
    await db.commit()


@router.get("/goals/{goal_id}/events", response_model=list[EventResponse])
async def goal_events(goal_id: UUID, db: DbSession, user: CurrentUser):
    await GoalService(db, user.id).get(goal_id)
    rows = await db.scalars(
        select(GoalEvent).where(GoalEvent.goal_id == goal_id).order_by(GoalEvent.created_at.desc())
    )
    return list(rows)


@router.get("/reviews/{review_id}/goals", response_model=GoalLinks)
async def get_review_goals(review_id: UUID, db: DbSession, user: CurrentUser):
    await ReviewService(db, user.id).get(review_id)
    ids = await db.scalars(select(ReviewGoal.goal_id).where(ReviewGoal.review_id == review_id))
    return GoalLinks(goal_ids=list(ids))


@router.put("/reviews/{review_id}/goals", response_model=GoalLinks)
async def set_review_goals(review_id: UUID, payload: GoalLinks, db: DbSession, user: CurrentUser):
    await GoalService(db, user.id).replace_review_links(review_id, payload.goal_ids)
    return payload
