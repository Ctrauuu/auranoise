from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, UUIDTimestampMixin


class Goal(UUIDTimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'active', 'completed', 'paused', 'abandoned')",
            name="ck_goals_status",
        ),
        Index("ix_goals_user_status", "user_id", "status"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    status: Mapped[str] = mapped_column(String(20), default="not_started", server_default="not_started")
    start_date: Mapped[date] = mapped_column(Date)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class GoalTask(UUIDTimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "goal_tasks"
    __table_args__ = (
        CheckConstraint("status IN ('todo', 'in_progress', 'completed')", name="ck_goal_tasks_status"),
        Index("ix_goal_tasks_goal_status", "goal_id", "status"),
    )

    goal_id: Mapped[UUID] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="todo", server_default="todo")


class GoalEvent(UUIDTimestampMixin, Base):
    __tablename__ = "goal_events"
    __table_args__ = (Index("ix_goal_events_goal_created", "goal_id", "created_at"),)

    goal_id: Mapped[UUID] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(40))
    event_data: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)


class ReviewGoal(UUIDTimestampMixin, Base):
    __tablename__ = "review_goals"
    __table_args__ = (UniqueConstraint("review_id", "goal_id", name="uq_review_goals_pair"),)

    review_id: Mapped[UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[UUID] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), index=True)

