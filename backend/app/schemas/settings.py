from pydantic import BaseModel, ConfigDict, Field, field_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timezone: str
    theme: str
    autosave_seconds: int
    markdown_view: str
    show_active_goals: bool
    show_tasks_due_today: bool
    trash_retention_days: int | None


class SettingsUpdate(BaseModel):
    timezone: str | None = None
    theme: str | None = Field(default=None, pattern="^(system|light|dark)$")
    autosave_seconds: int | None = Field(default=None, ge=2, le=10)
    markdown_view: str | None = Field(default=None, pattern="^(single|split)$")
    show_active_goals: bool | None = None
    show_tasks_due_today: bool | None = None
    trash_retention_days: int | None = Field(default=None)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str | None) -> str | None:
        if value:
            try:
                ZoneInfo(value)
            except ZoneInfoNotFoundError:
                raise ValueError("Unknown IANA timezone") from None
        return value

    @field_validator("trash_retention_days")
    @classmethod
    def valid_retention(cls, value: int | None) -> int | None:
        if value not in (None, 7, 30, 90):
            raise ValueError("Retention must be 7, 30, 90, or null")
        return value

