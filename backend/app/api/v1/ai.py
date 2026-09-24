from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.core.exceptions import AppError

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/weekly-summary")
async def weekly_summary(_: CurrentUser):
    raise AppError(501, "AI_NOT_ENABLED", "AI features are not enabled yet")

