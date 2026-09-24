from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Query, Response
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import AppError
from app.models.review import ReviewSectionPreset, ReviewSnapshot
from app.repositories.review import ReviewRepository
from app.schemas.review import (
    PaginatedReviews,
    PresetCreate,
    PresetResponse,
    ReorderSections,
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    SnapshotResponse,
    TemplateResponse,
    TemplateUpdate,
)
from app.services.review import ReviewService

router = APIRouter(tags=["reviews"])


@router.get("/reviews/today", response_model=ReviewResponse | None)
async def get_today(db: DbSession, user: CurrentUser):
    service = ReviewService(db, user.id)
    review = await service.reviews.get_by_date(user.id, await service.today())
    return await service.response(review) if review else None


@router.get("/reviews", response_model=PaginatedReviews)
async def list_reviews(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
):
    service = ReviewService(db, user.id)
    rows, total = await service.reviews.list(user.id, page, page_size, date_from, date_to)
    return PaginatedReviews(
        items=[await service.response(row) for row in rows], page=page, page_size=page_size, total=total
    )


@router.post("/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(payload: ReviewCreate, db: DbSession, user: CurrentUser):
    return await ReviewService(db, user.id).create(payload.review_date)


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: UUID, db: DbSession, user: CurrentUser):
    service = ReviewService(db, user.id)
    return await service.response(await service.get(review_id))


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(review_id: UUID, payload: ReviewUpdate, db: DbSession, user: CurrentUser):
    service = ReviewService(db, user.id)
    review = await service.get(review_id)
    if payload.status is not None:
        if payload.status == "completed" and review.status != "completed":
            raise AppError(409, "USE_COMPLETE_ENDPOINT", "Complete a review using the complete endpoint")
        review.status = payload.status
    await db.commit()
    return await service.response(review)


@router.post("/reviews/{review_id}/complete", response_model=ReviewResponse)
async def complete_review(review_id: UUID, db: DbSession, user: CurrentUser):
    return await ReviewService(db, user.id).complete(review_id)


@router.get("/reviews/{review_id}/snapshots", response_model=list[SnapshotResponse])
async def list_snapshots(review_id: UUID, db: DbSession, user: CurrentUser):
    await ReviewService(db, user.id).get(review_id)
    rows = await db.scalars(
        select(ReviewSnapshot)
        .where(ReviewSnapshot.review_id == review_id)
        .order_by(ReviewSnapshot.version.desc())
    )
    return list(rows)


@router.get("/reviews/{review_id}/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(review_id: UUID, snapshot_id: UUID, db: DbSession, user: CurrentUser):
    await ReviewService(db, user.id).get(review_id)
    snapshot = await db.scalar(
        select(ReviewSnapshot).where(
            ReviewSnapshot.id == snapshot_id,
            ReviewSnapshot.review_id == review_id,
        )
    )
    if not snapshot:
        raise AppError(404, "SNAPSHOT_NOT_FOUND", "Review snapshot not found")
    return snapshot


@router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(review_id: UUID, db: DbSession, user: CurrentUser):
    review = await ReviewService(db, user.id).get(review_id)
    review.deleted_at = datetime.now(UTC)
    await db.commit()


@router.post("/reviews/{review_id}/sections", response_model=SectionResponse, status_code=201)
async def add_section(review_id: UUID, payload: SectionCreate, db: DbSession, user: CurrentUser):
    return await ReviewService(db, user.id).add_section(review_id, payload)


@router.patch("/review-sections/{section_id}", response_model=SectionResponse)
async def update_section(section_id: UUID, payload: SectionUpdate, db: DbSession, user: CurrentUser):
    service = ReviewService(db, user.id)
    section = await service.owned_section(section_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(section, key, value)
    await db.commit()
    return SectionResponse.model_validate(section)


@router.delete("/review-sections/{section_id}", status_code=204)
async def delete_section(section_id: UUID, db: DbSession, user: CurrentUser):
    section = await ReviewService(db, user.id).owned_section(section_id)
    section.deleted_at = datetime.now(UTC)
    await db.commit()


@router.put("/reviews/{review_id}/sections/reorder", status_code=204)
async def reorder_sections(review_id: UUID, payload: ReorderSections, db: DbSession, user: CurrentUser):
    service = ReviewService(db, user.id)
    review = await service.get(review_id)
    sections = await service.reviews.sections(review.id)
    if set(payload.section_ids) != {section.id for section in sections}:
        raise AppError(422, "INVALID_SECTION_ORDER", "Section order must include every active section")
    by_id = {section.id: section for section in sections}
    for order, section_id in enumerate(payload.section_ids):
        by_id[section_id].sort_order = order
    await db.commit()


@router.get("/section-presets", response_model=list[PresetResponse])
async def list_presets(db: DbSession, user: CurrentUser):
    rows = await db.scalars(
        select(ReviewSectionPreset)
        .where(ReviewSectionPreset.user_id == user.id, ReviewSectionPreset.deleted_at.is_(None))
        .order_by(ReviewSectionPreset.title)
    )
    return list(rows)


@router.post("/section-presets", response_model=PresetResponse, status_code=201)
async def create_preset(payload: PresetCreate, db: DbSession, user: CurrentUser):
    preset = ReviewSectionPreset(user_id=user.id, title=payload.title)
    db.add(preset)
    await db.commit()
    return preset


@router.patch("/section-presets/{preset_id}", response_model=PresetResponse)
async def update_preset(preset_id: UUID, payload: PresetCreate, db: DbSession, user: CurrentUser):
    preset = await db.scalar(
        select(ReviewSectionPreset).where(
            ReviewSectionPreset.id == preset_id,
            ReviewSectionPreset.user_id == user.id,
            ReviewSectionPreset.deleted_at.is_(None),
        )
    )
    if not preset:
        raise AppError(404, "PRESET_NOT_FOUND", "Section preset not found")
    preset.title = payload.title
    await db.commit()
    return preset


@router.delete("/section-presets/{preset_id}", status_code=204)
async def delete_preset(preset_id: UUID, db: DbSession, user: CurrentUser):
    preset = await db.scalar(
        select(ReviewSectionPreset).where(
            ReviewSectionPreset.id == preset_id,
            ReviewSectionPreset.user_id == user.id,
            ReviewSectionPreset.deleted_at.is_(None),
        )
    )
    if not preset:
        raise AppError(404, "PRESET_NOT_FOUND", "Section preset not found")
    preset.deleted_at = datetime.now(UTC)
    await db.commit()


@router.get("/review-template", response_model=TemplateResponse)
async def get_template(db: DbSession, user: CurrentUser):
    template_id, items = await ReviewService(db, user.id).template()
    return TemplateResponse(id=template_id, items=items)


@router.put("/review-template", response_model=TemplateResponse)
async def update_template(payload: TemplateUpdate, db: DbSession, user: CurrentUser):
    service = ReviewService(db, user.id)
    template_id, _ = await service.template()
    normalized = [(item.title, order) for order, item in enumerate(payload.items)]
    await service.reviews.replace_template(template_id, normalized)
    await db.commit()
    template_id, items = await service.template()
    return TemplateResponse(id=template_id, items=items)
