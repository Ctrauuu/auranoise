from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import AppError
from app.models.user import UserSettings
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(db: DbSession, user: CurrentUser):
    settings = await db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if not settings:
        raise AppError(404, "SETTINGS_NOT_FOUND", "User settings not found")
    return settings


@router.patch("/settings", response_model=SettingsResponse)
async def update_settings(payload: SettingsUpdate, db: DbSession, user: CurrentUser):
    settings = await db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if not settings:
        raise AppError(404, "SETTINGS_NOT_FOUND", "User settings not found")
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(settings, key, value)
    await db.commit()
    return settings

