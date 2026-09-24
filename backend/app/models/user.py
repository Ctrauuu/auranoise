from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin


class User(UUIDTimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username"),)

    username: Mapped[str] = mapped_column(String(80), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class UserSettings(UUIDTimestampMixin, Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        UniqueConstraint("user_id"),
        CheckConstraint("theme IN ('system', 'light', 'dark')", name="ck_user_settings_theme"),
        CheckConstraint("markdown_view IN ('single', 'split')", name="ck_user_settings_markdown_view"),
        CheckConstraint("autosave_seconds BETWEEN 2 AND 10", name="ck_user_settings_autosave"),
        CheckConstraint("trash_retention_days IN (7, 30, 90) OR trash_retention_days IS NULL", name="ck_user_settings_retention"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timezone: Mapped[str] = mapped_column(String(80), default="UTC", server_default="UTC")
    theme: Mapped[str] = mapped_column(String(10), default="system", server_default="system")
    autosave_seconds: Mapped[int] = mapped_column(default=3, server_default="3")
    markdown_view: Mapped[str] = mapped_column(String(10), default="single", server_default="single")
    show_active_goals: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    show_tasks_due_today: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    trash_retention_days: Mapped[int | None] = mapped_column(default=30, server_default="30", nullable=True)
