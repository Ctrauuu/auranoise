from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TrashItem(BaseModel):
    type: str
    id: UUID
    title: str
    deleted_at: datetime
    metadata: dict[str, Any] = {}


class TrashResponse(BaseModel):
    items: list[TrashItem]
    page: int
    page_size: int
    total: int


class ImportSummary(BaseModel):
    schema_version: int
    reviews: int
    sections: int
    goals: int
    tasks: int
    confirmed: bool = False


class BackupPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    exported_at: datetime
    user_settings: dict[str, Any]
    review_template: dict[str, Any]
    section_presets: list[dict[str, Any]]
    reviews: list[dict[str, Any]]
    review_sections: list[dict[str, Any]]
    review_snapshots: list[dict[str, Any]]
    goals: list[dict[str, Any]]
    goal_tasks: list[dict[str, Any]]
    goal_events: list[dict[str, Any]]
    review_goal_relations: list[dict[str, Any]]
