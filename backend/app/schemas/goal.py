from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


GoalStatus = str
TaskStatus = str


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    status: GoalStatus = Field(default="not_started", pattern="^(not_started|active|completed|paused|abandoned)$")
    start_date: date
    target_date: date | None = None


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: GoalStatus | None = Field(default=None, pattern="^(not_started|active|completed|paused|abandoned)$")
    start_date: date | None = None
    target_date: date | None = None


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    due_date: date | None = None
    status: TaskStatus = Field(default="todo", pattern="^(todo|in_progress|completed)$")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    status: TaskStatus | None = Field(default=None, pattern="^(todo|in_progress|completed)$")


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    due_date: date | None
    status: str


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    status: str
    start_date: date
    target_date: date | None
    created_at: datetime
    updated_at: datetime
    tasks: list[TaskResponse] = []


class GoalList(BaseModel):
    items: list[GoalResponse]
    page: int
    page_size: int
    total: int


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    event_data: dict
    created_at: datetime


class GoalLinks(BaseModel):
    goal_ids: list[UUID]

