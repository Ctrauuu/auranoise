from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.discovery import SearchResponse, StatsSummary, TimelineResponse
from app.services.discovery import DiscoveryService

router = APIRouter(tags=["discovery"])


@router.get("/search", response_model=SearchResponse)
async def search(
    db: DbSession,
    user: CurrentUser,
    keyword: str = Query("", max_length=200),
    date_from: date | None = None,
    date_to: date | None = None,
    section_label: str | None = Query(None, max_length=120),
    result_type: str | None = Query(None, pattern="^(review|section|preset|goal|task)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    service = DiscoveryService(db, user.id)
    results, total = await service.search(keyword, result_type, date_from, date_to, section_label, page * page_size)
    start = (page - 1) * page_size
    return SearchResponse(items=results[start:start + page_size], page=page, page_size=page_size, total=total)


@router.get("/timeline", response_model=TimelineResponse)
async def timeline(
    db: DbSession,
    user: CurrentUser,
    type: str | None = Query(None, pattern="^(reviews|goals|tasks)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    entries, total = await DiscoveryService(db, user.id).timeline(type, page * page_size)
    start = (page - 1) * page_size
    return TimelineResponse(items=entries[start:start + page_size], page=page, page_size=page_size, total=total)


@router.get("/stats/summary", response_model=StatsSummary)
async def stats(db: DbSession, user: CurrentUser):
    return await DiscoveryService(db, user.id).stats()

