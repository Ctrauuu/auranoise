from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    preset_id: UUID | None
    title: str
    content_markdown: str
    sort_order: int


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    review_date: date
    status: str
    created_at: datetime
    updated_at: datetime
    sections: list[SectionResponse] = []


class ReviewCreate(BaseModel):
    review_date: date


class ReviewUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(draft|completed)$")


class SectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content_markdown: str = ""
    preset_id: UUID | None = None
    save_to_library: bool = False


class SectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content_markdown: str | None = None


class ReorderSections(BaseModel):
    section_ids: list[UUID]


class PresetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class PresetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str


class TemplateItem(BaseModel):
    id: UUID | None = None
    title: str = Field(min_length=1, max_length=120)
    sort_order: int = Field(ge=0)


class TemplateResponse(BaseModel):
    id: UUID
    items: list[TemplateItem]


class TemplateUpdate(BaseModel):
    items: list[TemplateItem] = Field(max_length=30)


class PaginatedReviews(BaseModel):
    items: list[ReviewResponse]
    page: int
    page_size: int
    total: int


class SnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    snapshot: dict
    created_at: datetime
