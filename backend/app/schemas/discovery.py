from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SearchResult(BaseModel):
    type: str
    id: UUID
    title: str
    snippet: str
    date: date | None
    metadata: dict[str, Any] = {}


class SearchResponse(BaseModel):
    items: list[SearchResult]
    page: int
    page_size: int
    total: int


class TimelineEntry(BaseModel):
    type: str
    id: UUID
    title: str
    occurred_at: datetime
    metadata: dict[str, Any] = {}


class TimelineResponse(BaseModel):
    items: list[TimelineEntry]
    page: int
    page_size: int
    total: int


class StatsSummary(BaseModel):
    reviews_completed_this_month: int
    current_review_streak: int
    longest_review_streak: int
    active_goals: int
    completed_goals: int
    goal_tasks_completed: int
    goal_tasks_total: int

