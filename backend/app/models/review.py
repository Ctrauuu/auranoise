from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, UUIDTimestampMixin


class Review(UUIDTimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "review_date", name="uq_reviews_user_date"),
        CheckConstraint("status IN ('draft', 'completed')", name="ck_reviews_status"),
        Index("ix_reviews_user_date", "user_id", "review_date"),
        Index("ix_reviews_user_status", "user_id", "status"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    review_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), default="draft", server_default="draft")


class ReviewSectionPreset(UUIDTimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "review_section_presets"
    __table_args__ = (Index("ix_presets_user_title", "user_id", "title"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))


class ReviewSection(UUIDTimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "review_sections"
    __table_args__ = (Index("ix_review_sections_order", "review_id", "sort_order"),)

    review_id: Mapped[UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"))
    preset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("review_section_presets.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(120))
    content_markdown: Mapped[str] = mapped_column(Text, default="", server_default="")
    sort_order: Mapped[int] = mapped_column(Integer)


class ReviewTemplate(UUIDTimestampMixin, Base):
    __tablename__ = "review_templates"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)


class ReviewTemplateItem(UUIDTimestampMixin, Base):
    __tablename__ = "review_template_items"
    __table_args__ = (Index("ix_template_items_order", "template_id", "sort_order"),)

    template_id: Mapped[UUID] = mapped_column(ForeignKey("review_templates.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(Integer)


class ReviewSnapshot(UUIDTimestampMixin, Base):
    __tablename__ = "review_snapshots"
    __table_args__ = (UniqueConstraint("review_id", "version", name="uq_snapshot_review_version"),)

    review_id: Mapped[UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
